from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class PreReminderPopup(QDialog):
    def __init__(self, minutes_left: int, auto_close_seconds: int, parent=None) -> None:
        super().__init__(parent)
        self.minutes_left = minutes_left
        self.auto_close_seconds = auto_close_seconds
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.close)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("SitReminder 预提醒")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.Tool, True)
        self.setModal(False)
        self.resize(320, 130)

        root = QVBoxLayout(self)
        root.setSpacing(10)

        text = QLabel(f"{self.minutes_left} 分钟后将正式提醒，建议提前准备起身活动。")
        text.setWordWrap(True)
        root.addWidget(text)

        row = QHBoxLayout()
        close_btn = QPushButton("知道了")
        close_btn.clicked.connect(self.close)
        row.addStretch(1)
        row.addWidget(close_btn)
        root.addLayout(row)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._move_to_bottom_right()
        self._close_timer.start(self.auto_close_seconds * 1000)

    def _move_to_bottom_right(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.x() + geo.width() - self.width() - 18
        y = geo.y() + geo.height() - self.height() - 18
        self.move(max(0, x), max(0, y))
