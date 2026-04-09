from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
)

from .config import AppConfig


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self._source_config = deepcopy(config)
        self._result_config: AppConfig | None = None
        self.setWindowTitle("SitReminder 设置")
        self.resize(500, 560)

        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.enabled_checkbox = QCheckBox("启用久坐提醒")
        form.addRow("提醒开关", self.enabled_checkbox)

        self.autostart_checkbox = QCheckBox("开机自动启动")
        form.addRow("开机自启", self.autostart_checkbox)

        self.sound_checkbox = QCheckBox("提醒时播放系统提示音")
        form.addRow("提示音", self.sound_checkbox)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("智能提醒模式", "smart")
        self.mode_combo.addItem("节律模式（工作/休息循环）", "cycle")
        self.mode_combo.currentIndexChanged.connect(self._update_mode_dependent_fields)
        form.addRow("提醒模式", self.mode_combo)

        self.interval_spin = self._spin(15, 240)
        form.addRow("提醒间隔(分钟)", self.interval_spin)

        self.cycle_work_spin = self._spin(15, 240)
        form.addRow("节律工作时长(分钟)", self.cycle_work_spin)

        self.cycle_rest_spin = self._spin(1, 60)
        form.addRow("节律休息时长(分钟)", self.cycle_rest_spin)

        self.pre_spin = self._spin(0, 30)
        form.addRow("预提醒提前(分钟)", self.pre_spin)

        self.pre_popup_checkbox = QCheckBox("预提醒时显示小弹窗（右下角自动消失）")
        form.addRow("预提醒弹窗", self.pre_popup_checkbox)

        self.pre_popup_seconds_spin = self._spin(3, 60)
        form.addRow("弹窗停留(秒)", self.pre_popup_seconds_spin)

        self.rest_spin = self._spin(1, 60)
        form.addRow("休息时长(分钟)", self.rest_spin)

        self.snooze_opts_input = QLineEdit()
        self.snooze_opts_input.setPlaceholderText("例如: 5,10,15")
        form.addRow("稍后提醒选项", self.snooze_opts_input)

        self.default_snooze_spin = self._spin(1, 240)
        form.addRow("默认稍后(分钟)", self.default_snooze_spin)

        self.max_snooze_spin = self._spin(1, 20)
        form.addRow("连续延期上限", self.max_snooze_spin)

        self.idle_spin = self._spin(1, 180)
        form.addRow("空闲重置阈值(分钟)", self.idle_spin)

        self.work_start_edit = self._time_edit()
        self.work_end_edit = self._time_edit()
        self.lunch_start_edit = self._time_edit()
        self.lunch_end_edit = self._time_edit()

        form.addRow("工作开始", self.work_start_edit)
        form.addRow("工作结束", self.work_end_edit)
        form.addRow("午休开始", self.lunch_start_edit)
        form.addRow("午休结束", self.lunch_end_edit)

        self.meeting_keywords_input = QLineEdit()
        self.meeting_keywords_input.setPlaceholderText("例如: teams, zoom, webex")
        form.addRow("会议应用关键词", self.meeting_keywords_input)

        root.addLayout(form)

        tip = QLabel(
            "说明：时间都支持自定义，工作/午休时段支持跨天，会议关键词用于前台进程识别。"
        )
        tip.setStyleSheet("color: #666;")
        tip.setWordWrap(True)
        root.addWidget(tip)

        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_save_clicked)
        btn_box.rejected.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_box)
        root.addLayout(btn_row)

    def _load_values(self) -> None:
        c = self._source_config
        self.enabled_checkbox.setChecked(c.enabled)
        self.autostart_checkbox.setChecked(c.autostart)
        self.sound_checkbox.setChecked(c.enable_sound)
        self.interval_spin.setValue(c.reminder_interval_minutes)
        self.pre_spin.setValue(c.pre_reminder_minutes)
        self.pre_popup_checkbox.setChecked(c.pre_reminder_use_popup)
        self.pre_popup_seconds_spin.setValue(c.pre_reminder_popup_seconds)
        self.rest_spin.setValue(c.rest_duration_minutes)
        self.snooze_opts_input.setText(",".join(str(x) for x in c.snooze_options_minutes))
        self.default_snooze_spin.setValue(c.default_snooze_minutes)
        self.max_snooze_spin.setValue(c.max_consecutive_snoozes)
        self.idle_spin.setValue(c.idle_reset_minutes)

        self.work_start_edit.setTime(self._parse_time(c.work_start))
        self.work_end_edit.setTime(self._parse_time(c.work_end))
        self.lunch_start_edit.setTime(self._parse_time(c.lunch_start))
        self.lunch_end_edit.setTime(self._parse_time(c.lunch_end))

        self.meeting_keywords_input.setText(", ".join(c.meeting_process_keywords))
        self._set_combo_by_data(self.mode_combo, c.reminder_mode)
        self.cycle_work_spin.setValue(c.cycle_work_minutes)
        self.cycle_rest_spin.setValue(c.cycle_rest_minutes)
        self._update_mode_dependent_fields()

    def build_config(self) -> AppConfig:
        cfg = AppConfig()

        cfg.enabled = self.enabled_checkbox.isChecked()
        cfg.autostart = self.autostart_checkbox.isChecked()
        cfg.enable_sound = self.sound_checkbox.isChecked()
        cfg.reminder_mode = self.mode_combo.currentData()

        cfg.reminder_interval_minutes = self.interval_spin.value()
        cfg.cycle_work_minutes = self.cycle_work_spin.value()
        cfg.cycle_rest_minutes = self.cycle_rest_spin.value()
        cfg.pre_reminder_minutes = self.pre_spin.value()
        cfg.pre_reminder_use_popup = self.pre_popup_checkbox.isChecked()
        cfg.pre_reminder_popup_seconds = self.pre_popup_seconds_spin.value()
        cfg.rest_duration_minutes = self.rest_spin.value()

        cfg.snooze_options_minutes = self._parse_int_list(self.snooze_opts_input.text())
        cfg.default_snooze_minutes = self.default_snooze_spin.value()
        cfg.max_consecutive_snoozes = self.max_snooze_spin.value()

        cfg.idle_reset_minutes = self.idle_spin.value()

        cfg.work_start = self.work_start_edit.time().toString("HH:mm")
        cfg.work_end = self.work_end_edit.time().toString("HH:mm")
        cfg.lunch_start = self.lunch_start_edit.time().toString("HH:mm")
        cfg.lunch_end = self.lunch_end_edit.time().toString("HH:mm")

        cfg.meeting_process_keywords = [
            token.strip().lower()
            for token in self.meeting_keywords_input.text().split(",")
            if token.strip()
        ]

        cfg._normalize()
        return cfg

    def result_config(self) -> AppConfig:
        return self._result_config if self._result_config is not None else self.build_config()

    def _on_save_clicked(self) -> None:
        cfg = self.build_config()

        current_work_minutes = (
            cfg.cycle_work_minutes if cfg.reminder_mode == "cycle" else cfg.reminder_interval_minutes
        )
        if cfg.pre_reminder_minutes >= current_work_minutes and cfg.pre_reminder_minutes > 0:
            QMessageBox.warning(
                self,
                "参数校验失败",
                "预提醒提前时间必须小于当前工作阶段时长，或设置为 0（关闭预提醒）。",
            )
            return

        self._result_config = cfg
        self.accept()

    def _update_mode_dependent_fields(self) -> None:
        is_smart = self.mode_combo.currentData() == "smart"
        self.interval_spin.setEnabled(is_smart)
        self.cycle_work_spin.setEnabled(not is_smart)
        self.cycle_rest_spin.setEnabled(not is_smart)

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    @staticmethod
    def _spin(low: int, high: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(low, high)
        return spin

    @staticmethod
    def _time_edit() -> QTimeEdit:
        edit = QTimeEdit()
        edit.setDisplayFormat("HH:mm")
        return edit

    @staticmethod
    def _parse_time(raw: str) -> QTime:
        t = QTime.fromString(raw, "HH:mm")
        return t if t.isValid() else QTime(9, 0)

    @staticmethod
    def _parse_int_list(raw: str) -> list[int]:
        values: list[int] = []
        for token in raw.replace(" ", "").split(","):
            if not token:
                continue
            try:
                values.append(int(token))
            except ValueError:
                continue
        return values
