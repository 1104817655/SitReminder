from __future__ import annotations

import logging
import sys
from datetime import datetime, time, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from .config import AppConfig, CONFIG_PATH
from .logging_setup import setup_logging
from .pre_reminder_popup import PreReminderPopup
from .reminder_dialog import ReminderDialog
from .rest_finished_popup import RestFinishedPopup
from .settings_dialog import SettingsDialog
from .stats_dialog import StatsDialog
from .stats_store import StatsStore
from .windows_startup import set_autostart
from .windows_state import get_idle_seconds, is_foreground_fullscreen, is_meeting_related

logger = logging.getLogger(__name__)


class SitReminderController(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self._is_first_run = not CONFIG_PATH.exists()
        self.config = AppConfig.load()
        self.stats_store = StatsStore()
        self._stats_dialog: StatsDialog | None = None

        self._mute_today: datetime.date | None = None
        self._paused_until: datetime | None = None
        self._deferred_due = False
        self._dialog_open = False
        self._was_idle = False
        self._was_in_work_period = False
        self._consecutive_snoozes = 0
        self._last_tick_at: datetime | None = None
        self._pre_popup: PreReminderPopup | None = None
        self._rest_done_popup: RestFinishedPopup | None = None
        self._cycle_phase = "work"
        self._cycle_phase_end_at: datetime | None = None

        self.next_reminder_at: datetime | None = None
        self.next_pre_reminder_at: datetime | None = None
        self.pre_sent = True

        self.tray = self._create_tray()
        self._apply_autostart()
        self._reset_cycle(anchor=datetime.now(), reset_snoozes=True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(1000)

        self._notify("SitReminder 已启动", "程序已在托盘运行。")
        self._refresh_tray_tooltip(datetime.now(), suppress=False)
        if self._is_first_run:
            QTimer.singleShot(500, lambda: self._open_settings(first_run=True))

    def _create_tray(self) -> QSystemTrayIcon:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("系统托盘不可用，无法运行 SitReminder。")

        icon = _load_app_icon(self.app)
        tray = QSystemTrayIcon(icon, self.app)

        menu = QMenu()

        self.enabled_action = QAction("启用提醒", self)
        self.enabled_action.setCheckable(True)
        self.enabled_action.setChecked(self.config.enabled)
        self.enabled_action.toggled.connect(self._toggle_enabled)
        menu.addAction(self.enabled_action)

        pause_action = QAction("暂停 30 分钟", self)
        pause_action.triggered.connect(self._pause_30m)
        menu.addAction(pause_action)

        mute_today_action = QAction("今日不提醒", self)
        mute_today_action.triggered.connect(self._mute_for_today)
        menu.addAction(mute_today_action)

        rest_now_action = QAction("立即开始休息", self)
        rest_now_action.triggered.connect(self._start_rest)
        menu.addAction(rest_now_action)

        stats_action = QAction("今日统计", self)
        stats_action.triggered.connect(self._open_stats)
        menu.addAction(stats_action)

        menu.addSeparator()

        settings_action = QAction("打开设置", self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.setToolTip("SitReminder")
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    def _apply_autostart(self) -> None:
        try:
            set_autostart(self.config.autostart)
        except Exception as exc:  # pragma: no cover - system-dependent
            logger.exception("设置开机自启失败: %s", exc)

    def _notify(self, title: str, message: str, timeout_ms: int = 4000) -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.Information, timeout_ms)

    def _toggle_enabled(self, enabled: bool) -> None:
        self.config.enabled = enabled
        self.config.save()
        if enabled:
            self._reset_cycle(anchor=datetime.now(), reset_snoozes=True)
            self._notify("提醒已开启", "久坐计时已重新开始。")
        else:
            self._notify("提醒已关闭", "你可以在托盘中随时重新开启。")
        self._refresh_tray_tooltip(datetime.now(), suppress=False)

    def _pause_30m(self) -> None:
        self._paused_until = datetime.now() + timedelta(minutes=30)
        self._notify("已暂停", "30 分钟内不再提醒。")
        self._refresh_tray_tooltip(datetime.now(), suppress=False)

    def _mute_for_today(self) -> None:
        self._mute_today = datetime.now().date()
        self._notify("今日不提醒", "今天剩余时间不再弹窗。")
        self._refresh_tray_tooltip(datetime.now(), suppress=False)

    def _start_rest(self) -> None:
        if self.config.reminder_mode == "cycle":
            self._start_cycle_rest_phase(anchor=datetime.now(), notify=True)
            self._refresh_tray_tooltip(datetime.now(), suppress=False)
            return

        self.stats_store.increment("rest_count")
        self._paused_until = datetime.now() + timedelta(minutes=self.config.rest_duration_minutes)
        self._reset_cycle(anchor=datetime.now(), reset_snoozes=True)
        self._notify("开始休息", f"已进入 {self.config.rest_duration_minutes} 分钟休息时间。")
        self._refresh_tray_tooltip(datetime.now(), suppress=False)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self._open_settings()

    def _open_settings(self, first_run: bool = False) -> None:
        dlg = SettingsDialog(self.config)
        if dlg.exec() == SettingsDialog.Accepted:
            self.config = dlg.result_config()
            self.config.save()
            self.enabled_action.setChecked(self.config.enabled)
            self._apply_autostart()
            self._reset_cycle(anchor=datetime.now(), reset_snoozes=True)
            self._notify("设置已保存", "新配置已生效。")
            self._refresh_tray_tooltip(datetime.now(), suppress=False)
            return

        if first_run:
            self._notify("可稍后设置", "你可以通过托盘双击或右键菜单打开设置。")

    def _open_stats(self) -> None:
        if self._stats_dialog is None:
            self._stats_dialog = StatsDialog(self.stats_store)
        self._stats_dialog.refresh()
        self._stats_dialog.show()
        self._stats_dialog.raise_()
        self._stats_dialog.activateWindow()

    def _reset_cycle(self, anchor: datetime, reset_snoozes: bool) -> None:
        if self.config.reminder_mode == "cycle":
            self._start_cycle_work_phase(anchor=anchor, reset_snoozes=reset_snoozes)
            return

        if reset_snoozes:
            self._consecutive_snoozes = 0

        self._deferred_due = False
        self._cycle_phase = "work"
        self._cycle_phase_end_at = None
        self.next_reminder_at = anchor + timedelta(minutes=self.config.reminder_interval_minutes)
        self._schedule_pre_reminder(self.next_reminder_at, now=anchor)

    def _on_tick(self) -> None:
        now = datetime.now()
        suppress = False
        if (
            self._last_tick_at is not None
            and (now - self._last_tick_at).total_seconds() >= 120
        ):
            self._reset_cycle(anchor=now, reset_snoozes=False)
            logger.info("检测到系统唤醒或长暂停，已重新对齐提醒计时。")
        self._last_tick_at = now

        try:
            if self._mute_today == now.date():
                return

            if not self.config.enabled:
                return

            if self._paused_until is not None:
                if now < self._paused_until:
                    return
                self._paused_until = None

            in_work_period = self._in_work_period(now.time())
            if not in_work_period:
                self._was_in_work_period = False
                return
            if not self._was_in_work_period:
                self._was_in_work_period = True
                self._reset_cycle(anchor=now, reset_snoozes=True)
                return

            if not (self.config.reminder_mode == "cycle" and self._cycle_phase == "rest"):
                idle_seconds = get_idle_seconds()
                idle_threshold = self.config.idle_reset_minutes * 60

                if idle_seconds >= idle_threshold and not self._was_idle:
                    self._was_idle = True
                    self.stats_store.increment("idle_reset_count")
                    self._reset_cycle(anchor=now, reset_snoozes=True)
                    logger.info("用户空闲超过阈值，已重置久坐计时。")
                    return

                if idle_seconds < idle_threshold:
                    self._was_idle = False

            if self.config.reminder_mode == "cycle":
                suppress = self._tick_cycle_mode(now)
            else:
                suppress = self._tick_smart_mode(now)
        finally:
            self._refresh_tray_tooltip(now, suppress=suppress)

    def _tick_smart_mode(self, now: datetime) -> bool:
        suppress = is_foreground_fullscreen() or is_meeting_related(
            self.config.meeting_process_keywords
        )

        if self.next_reminder_at is None:
            self._reset_cycle(anchor=now, reset_snoozes=False)
            return suppress

        if suppress:
            if now >= self.next_reminder_at:
                if not self._deferred_due:
                    self.stats_store.increment("deferred_count")
                self._deferred_due = True
            return suppress

        if self._deferred_due and not self._dialog_open:
            self._deferred_due = False
            self._show_reminder(strong=self._is_strong_mode())
            return suppress

        if (
            not self.pre_sent
            and self.next_pre_reminder_at is not None
            and now >= self.next_pre_reminder_at
        ):
            self.pre_sent = True
            self._show_pre_reminder()

        if now >= self.next_reminder_at and not self._dialog_open:
            self._show_reminder(strong=self._is_strong_mode())
        return suppress

    def _tick_cycle_mode(self, now: datetime) -> bool:
        if self._cycle_phase_end_at is None:
            self._start_cycle_work_phase(anchor=now, reset_snoozes=False)
            return False

        if self._cycle_phase == "rest":
            if now >= self._cycle_phase_end_at:
                self._finish_cycle_rest_phase(now)
            return False

        suppress = is_foreground_fullscreen() or is_meeting_related(
            self.config.meeting_process_keywords
        )
        if suppress:
            if now >= self._cycle_phase_end_at:
                if not self._deferred_due:
                    self.stats_store.increment("deferred_count")
                self._deferred_due = True
            return True

        if self._deferred_due and not self._dialog_open:
            self._deferred_due = False
            self._show_reminder(strong=self._is_strong_mode())
            return False

        if (
            not self.pre_sent
            and self.next_pre_reminder_at is not None
            and now >= self.next_pre_reminder_at
        ):
            self.pre_sent = True
            self._show_pre_reminder()

        if now >= self._cycle_phase_end_at and not self._dialog_open:
            self._show_reminder(strong=self._is_strong_mode())
        return False

    def _start_cycle_work_phase(self, anchor: datetime, reset_snoozes: bool) -> None:
        if reset_snoozes:
            self._consecutive_snoozes = 0

        self._cycle_phase = "work"
        self._deferred_due = False
        self._cycle_phase_end_at = anchor + timedelta(minutes=self.config.cycle_work_minutes)
        self.next_reminder_at = self._cycle_phase_end_at
        self._schedule_pre_reminder(self._cycle_phase_end_at, now=anchor)

    def _start_cycle_rest_phase(self, anchor: datetime, notify: bool) -> None:
        self.stats_store.increment("rest_count")
        self._cycle_phase = "rest"
        self._consecutive_snoozes = 0
        self._deferred_due = False
        self._cycle_phase_end_at = anchor + timedelta(minutes=self.config.cycle_rest_minutes)
        self.next_reminder_at = self._cycle_phase_end_at
        self.next_pre_reminder_at = None
        self.pre_sent = True
        if notify:
            self._notify("开始休息", f"已进入 {self.config.cycle_rest_minutes} 分钟休息时间。")

    def _finish_cycle_rest_phase(self, now: datetime) -> None:
        self._notify("休息完成", "休息结束，已自动进入下一轮工作。")
        if self._rest_done_popup is not None and self._rest_done_popup.isVisible():
            self._rest_done_popup.close()
        self._rest_done_popup = RestFinishedPopup(auto_close_seconds=10)
        self._rest_done_popup.show()
        self._start_cycle_work_phase(anchor=now, reset_snoozes=True)

    def _schedule_pre_reminder(self, target_at: datetime, now: datetime) -> None:
        if self.config.pre_reminder_minutes > 0:
            self.next_pre_reminder_at = target_at - timedelta(
                minutes=self.config.pre_reminder_minutes
            )
            self.pre_sent = self.next_pre_reminder_at <= now
        else:
            self.next_pre_reminder_at = None
            self.pre_sent = True

    def _show_pre_reminder(self) -> None:
        if self.config.pre_reminder_use_popup:
            if self._pre_popup is not None and self._pre_popup.isVisible():
                self._pre_popup.close()
            self._pre_popup = PreReminderPopup(
                minutes_left=self.config.pre_reminder_minutes,
                auto_close_seconds=self.config.pre_reminder_popup_seconds,
            )
            self._pre_popup.show()
            return

        self._notify(
            "即将提醒",
            f"{self.config.pre_reminder_minutes} 分钟后请起身活动一下。",
        )

    def _show_reminder(self, strong: bool) -> None:
        self.stats_store.increment("reminder_count")
        self._dialog_open = True
        dialog = ReminderDialog(self.config, strong=strong)
        dialog.exec()
        self._dialog_open = False

        action, value = dialog.result_action
        now = datetime.now()

        if action == "rest":
            self._start_rest()
            return

        if action == "skip":
            self.stats_store.increment("skip_count")
            self._reset_cycle(anchor=now, reset_snoozes=True)
            logger.info("用户跳过本次提醒。")
            return

        if action == "snooze":
            if self._consecutive_snoozes >= self.config.max_consecutive_snoozes:
                self._notify("延期已达上限", "请先起身活动，再继续工作。")
                self._show_reminder(strong=True)
                return

            snooze_minutes = value or self.config.default_snooze_minutes
            self._consecutive_snoozes += 1
            self.stats_store.increment("snooze_count")
            self.next_reminder_at = now + timedelta(minutes=snooze_minutes)
            if self.config.reminder_mode == "cycle":
                self._cycle_phase = "work"
                self._cycle_phase_end_at = self.next_reminder_at
            self._schedule_pre_reminder(self.next_reminder_at, now=now)

            logger.info("用户延期提醒 %s 分钟，连续延期次数=%s", snooze_minutes, self._consecutive_snoozes)
            return

        self._reset_cycle(anchor=now, reset_snoozes=False)

    def _is_strong_mode(self) -> bool:
        return self._consecutive_snoozes >= self.config.max_consecutive_snoozes

    def _refresh_tray_tooltip(self, now: datetime, suppress: bool) -> None:
        lines = ["SitReminder"]
        mode_name = "节律模式" if self.config.reminder_mode == "cycle" else "智能模式"
        lines.append(f"模式: {mode_name}")

        if not self.config.enabled:
            lines.append("状态: 已关闭")
        elif self._mute_today == now.date():
            lines.append("状态: 今日不提醒")
        elif self._paused_until is not None and now < self._paused_until:
            lines.append(f"状态: 已暂停至 {self._paused_until:%H:%M}")
        else:
            lines.append("状态: 运行中")

        if (
            self.config.enabled
            and self.config.reminder_mode == "cycle"
            and self._cycle_phase_end_at is not None
        ):
            phase_text = "工作中" if self._cycle_phase == "work" else "休息中"
            lines.append(f"阶段: {phase_text}")
            lines.append(f"本阶段剩余: {_format_remaining(self._cycle_phase_end_at - now)}")
            lines.append(f"阶段结束: {self._cycle_phase_end_at:%H:%M}")
        elif self.next_reminder_at is not None and self.config.enabled:
            lines.append(f"下次提醒: {self.next_reminder_at:%H:%M}")
        if (
            self.next_pre_reminder_at is not None
            and not self.pre_sent
            and self.config.pre_reminder_minutes > 0
            and self.config.enabled
        ):
            lines.append(f"预提醒: {self.next_pre_reminder_at:%H:%M}")
        if suppress:
            lines.append("场景: 全屏/会议静默")
        lines.append(f"连续延期: {self._consecutive_snoozes}/{self.config.max_consecutive_snoozes}")

        self.tray.setToolTip("\n".join(lines))

    def _in_work_period(self, current: time) -> bool:
        work_start = _parse_hhmm(self.config.work_start)
        work_end = _parse_hhmm(self.config.work_end)
        lunch_start = _parse_hhmm(self.config.lunch_start)
        lunch_end = _parse_hhmm(self.config.lunch_end)

        in_work = _in_time_range(work_start, work_end, current)
        in_lunch = _in_time_range(lunch_start, lunch_end, current)
        return in_work and not in_lunch


def _parse_hhmm(raw: str) -> time:
    hour, minute = [int(x) for x in raw.split(":")]
    return time(hour=hour, minute=minute)


def _in_time_range(start: time, end: time, current: time) -> bool:
    if start == end:
        return False
    if start < end:
        return start <= current < end
    return current >= start or current < end


def _format_remaining(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    if seconds < 0:
        seconds = 0
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def _resource_base_dir() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _load_app_icon(app: QApplication) -> QIcon:
    icon_path = _resource_base_dir() / "resources" / "icon.ico"
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        app.setWindowIcon(icon)
        return icon
    return app.style().standardIcon(QStyle.SP_ComputerIcon)


def main() -> int:
    setup_logging()
    logger.info("SitReminder 启动")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    try:
        _controller = SitReminderController(app)
    except Exception as exc:
        logger.exception("启动失败: %s", exc)
        return 1

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
