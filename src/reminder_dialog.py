from __future__ import annotations

import os

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QMenu,
)

from .config import AppConfig

if os.name == "nt":
    import winsound


class ReminderDialog(QDialog):
    def __init__(self, config: AppConfig, strong: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.strong = strong
        self.result_action: tuple[str, int | None] = ("skip", None)
        self._beep_timer: QTimer | None = None

        self._build_ui()

        if self.strong and self.config.enable_sound and os.name == "nt":
            self._beep_timer = QTimer(self)
            self._beep_timer.timeout.connect(self._play_beep)
            self._beep_timer.start(8000)
            self._play_beep()

    def _build_ui(self) -> None:
        self.setWindowTitle("SitReminder")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setModal(True)
        self.resize(460, 240)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        msg = "该起身活动一下了，建议现在休息几分钟。"
        if self.strong:
            msg = "你已多次延期提醒，请先起身活动后再继续工作。"

        label = QLabel(msg)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(label)

        if self.strong:
            warn = QLabel("强提醒模式：已禁用“稍后提醒”。")
            warn.setStyleSheet("color: #b22222; font-weight: 600;")
            layout.addWidget(warn)

        btn_row = QHBoxLayout()

        rest_btn = QPushButton("开始休息")
        rest_btn.clicked.connect(self._choose_rest)
        btn_row.addWidget(rest_btn)

        self.snooze_btn = QToolButton()
        self.snooze_btn.setText("稍后提醒")
        self.snooze_btn.setPopupMode(QToolButton.InstantPopup)
        self.snooze_btn.setEnabled(not self.strong)

        snooze_menu = QMenu(self)
        for minutes in self.config.snooze_options_minutes:
            action = snooze_menu.addAction(f"{minutes} 分钟")
            action.triggered.connect(lambda checked=False, m=minutes: self._choose_snooze(m))
        self.snooze_btn.setMenu(snooze_menu)
        btn_row.addWidget(self.snooze_btn)

        skip_btn = QPushButton("跳过本次")
        skip_btn.clicked.connect(self._choose_skip)
        btn_row.addWidget(skip_btn)

        layout.addLayout(btn_row)

        if not self.strong:
            custom_row = QHBoxLayout()
            custom_label = QLabel("本次自定义稍后(分钟)")
            custom_row.addWidget(custom_label)

            self.custom_snooze_spin = QSpinBox()
            self.custom_snooze_spin.setRange(1, 240)
            self.custom_snooze_spin.setValue(self.config.default_snooze_minutes)
            custom_row.addWidget(self.custom_snooze_spin)

            custom_btn = QPushButton("本次稍后")
            custom_btn.clicked.connect(self._choose_custom_snooze)
            custom_row.addWidget(custom_btn)

            layout.addLayout(custom_row)

        hint = QLabel("你也可以通过系统托盘临时暂停 30 分钟。")
        hint.setStyleSheet("color: #555;")
        layout.addWidget(hint)

    def _play_beep(self) -> None:
        if os.name == "nt":
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    def _stop_beep(self) -> None:
        if self._beep_timer is not None:
            self._beep_timer.stop()

    def _choose_rest(self) -> None:
        self.result_action = ("rest", None)
        self._stop_beep()
        self.accept()

    def _choose_snooze(self, minutes: int) -> None:
        self.result_action = ("snooze", minutes)
        self._stop_beep()
        self.accept()

    def _choose_custom_snooze(self) -> None:
        self._choose_snooze(self.custom_snooze_spin.value())

    def _choose_skip(self) -> None:
        self.result_action = ("skip", None)
        self._stop_beep()
        self.accept()
