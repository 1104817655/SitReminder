from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class RestFinishedPopup(QDialog):
    def __init__(self, auto_close_seconds: int = 10, parent=None) -> None:
        super().__init__(parent)
        self.auto_close_seconds = auto_close_seconds
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.close)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("SitReminder")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.Tool, True)
        self.setModal(False)
        self.resize(320, 120)

        root = QVBoxLayout(self)
        root.setSpacing(10)

        text = QLabel("休息时间结束，已自动开始下一轮工作。")
        text.setWordWrap(True)
        root.addWidget(text)

        row = QHBoxLayout()
        ok_btn = QPushButton("知道了")
        ok_btn.clicked.connect(self.close)
        row.addStretch(1)
        row.addWidget(ok_btn)
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
