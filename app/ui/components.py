from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.action_model import Action


def page_header(title: str, subtitle: str = "") -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 12)
    title_label = QLabel(title)
    title_label.setObjectName("PageTitle")
    layout.addWidget(title_label)
    if subtitle:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("MutedText")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
    return widget


def card(title: str, body: str = "") -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    heading = QLabel(title)
    heading.setObjectName("CardTitle")
    layout.addWidget(heading)
    if body:
        label = QLabel(body)
        label.setWordWrap(True)
        layout.addWidget(label)
    return frame


def risk_badge(risk: str) -> QLabel:
    label = QLabel(risk.upper())
    label.setProperty("risk", risk)
    label.setObjectName("RiskBadge")
    label.setAlignment(Qt.AlignCenter)
    return label


class ActionChecklist(QWidget):
    def __init__(self, actions: Iterable[Action]) -> None:
        super().__init__()
        self.actions = list(actions)
        self._checks: dict[str, QCheckBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for action in self.actions:
            row = QFrame()
            row.setObjectName("ActionRow")
            row_layout = QHBoxLayout(row)
            check = QCheckBox()
            check.setChecked(action.default_selected)
            if action.is_risky_or_expert:
                check.setChecked(False)
            self._checks[action.id] = check
            text = QLabel(f"{action.title}\n{action.description}")
            text.setWordWrap(True)
            row_layout.addWidget(check)
            row_layout.addWidget(text, 1)
            row_layout.addWidget(risk_badge(action.risk_level))
            layout.addWidget(row)
        layout.addStretch(1)

    def selected_actions(self) -> list[Action]:
        return [action for action in self.actions if self._checks[action.id].isChecked()]

    def clear_selection(self) -> None:
        for check in self._checks.values():
            check.setChecked(False)

    def select_safe_only(self) -> None:
        for action in self.actions:
            self._checks[action.id].setChecked(action.risk_level == "safe")


class ReportList(QListWidget):
    def set_paths(self, paths: Iterable[str]) -> None:
        self.clear()
        for path in paths:
            item = QListWidgetItem(path)
            self.addItem(item)


def button_row(*buttons: QPushButton) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    for button in buttons:
        layout.addWidget(button)
    layout.addStretch(1)
    return widget
