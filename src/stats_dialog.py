from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QPushButton, QVBoxLayout

from .stats_store import StatsStore


class StatsDialog(QDialog):
    def __init__(self, stats_store: StatsStore, parent=None) -> None:
        super().__init__(parent)
        self.stats_store = stats_store
        self.setWindowTitle("SitReminder 今日统计")
        self.resize(360, 260)

        self._value_labels: dict[str, QLabel] = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        form = QFormLayout()
        form.setVerticalSpacing(10)

        self._add_row(form, "提醒次数", "reminder_count")
        self._add_row(form, "休息次数", "rest_count")
        self._add_row(form, "延期次数", "snooze_count")
        self._add_row(form, "跳过次数", "skip_count")
        self._add_row(form, "静默补发次数", "deferred_count")
        self._add_row(form, "空闲重置次数", "idle_reset_count")

        self.rate_label = QLabel("-")
        form.addRow("执行率", self.rate_label)

        root.addLayout(form)

        self.day_label = QLabel("")
        self.day_label.setStyleSheet("color: #666;")
        root.addWidget(self.day_label)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh)
        root.addWidget(refresh_btn)

    def _add_row(self, form: QFormLayout, title: str, key: str) -> None:
        label = QLabel("0")
        self._value_labels[key] = label
        form.addRow(title, label)

    def refresh(self) -> None:
        daily = self.stats_store.get_daily(date.today())
        for key, label in self._value_labels.items():
            label.setText(str(getattr(daily, key)))

        if daily.reminder_count > 0:
            rate = int((daily.rest_count / daily.reminder_count) * 100)
            self.rate_label.setText(f"{rate}%")
        else:
            self.rate_label.setText("-")

        self.day_label.setText(f"日期：{daily.day}")
