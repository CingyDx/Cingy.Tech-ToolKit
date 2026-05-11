from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.action_model import Action
from app.core.modes import ModeDefinition, friendly_action_title


RISK_LABELS = {
    "safe": "Bezpečné",
    "moderate": "Střední",
    "risky": "Rizikové",
    "expert": "Expert",
}


def make_scroll_area(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    return scroll


def page_header(title: str, subtitle: str = "") -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 18)
    layout.setSpacing(8)
    title_label = QLabel(title)
    title_label.setObjectName("PageTitle")
    title_label.setWordWrap(True)
    layout.addWidget(title_label)
    if subtitle:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
    return widget


def primary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("PrimaryButton")
    button.setCursor(Qt.PointingHandCursor)
    return button


def secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("SecondaryButton")
    button.setCursor(Qt.PointingHandCursor)
    return button


def ghost_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("GhostButton")
    button.setCursor(Qt.PointingHandCursor)
    return button


class SectionCard(QFrame):
    def __init__(self, title: str, body: str = "", *, accent: bool = False) -> None:
        super().__init__()
        self.setObjectName("SectionCardAccent" if accent else "SectionCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(22, 20, 22, 20)
        self.layout.setSpacing(12)
        heading = QLabel(title)
        heading.setObjectName("CardTitle")
        heading.setWordWrap(True)
        self.layout.addWidget(heading)
        if body:
            label = QLabel(body)
            label.setObjectName("MutedText")
            label.setWordWrap(True)
            self.layout.addWidget(label)


def card(title: str, body: str = "") -> QFrame:
    return SectionCard(title, body)


class StatusPill(QLabel):
    def __init__(self, text: str, tone: str = "neutral") -> None:
        super().__init__(text)
        self.setObjectName("StatusPill")
        self.setProperty("tone", tone)
        self.setAlignment(Qt.AlignCenter)


def risk_badge(risk: str) -> QLabel:
    label = QLabel(RISK_LABELS.get(risk, risk).upper())
    label.setProperty("risk", risk)
    label.setObjectName("RiskBadge")
    label.setAlignment(Qt.AlignCenter)
    return label


class EmptyState(QFrame):
    def __init__(self, title: str, body: str) -> None:
        super().__init__()
        self.setObjectName("EmptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        heading = QLabel(title)
        heading.setObjectName("EmptyTitle")
        heading.setWordWrap(True)
        message = QLabel(body)
        message.setObjectName("MutedText")
        message.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(message)


class ModeCard(QFrame):
    selected = Signal(str)

    def __init__(self, mode: ModeDefinition) -> None:
        super().__init__()
        self.mode = mode
        self.setObjectName("ModeCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(205)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        top = QHBoxLayout()
        icon = QLabel(_icon_text(mode.icon))
        icon.setObjectName("ModeIcon")
        title = QLabel(mode.title_cs)
        title.setObjectName("ModeTitle")
        title.setWordWrap(True)
        top.addWidget(icon)
        top.addWidget(title, 1)
        top.addWidget(risk_badge(mode.risk))
        layout.addLayout(top)

        body = QLabel(mode.short_description_cs)
        body.setObjectName("ModeDescription")
        body.setWordWrap(True)
        layout.addWidget(body)

        badge_row = QHBoxLayout()
        if mode.id == "safe_cleanup":
            badge_row.addWidget(StatusPill("Doporučeno", "good"))
        for item in mode.recommended_for[:1]:
            badge_row.addWidget(StatusPill(item, "neutral"))
        badge_row.addStretch(1)
        layout.addLayout(badge_row)

        layout.addStretch(1)
        button = secondary_button("Vybrat režim")
        button.clicked.connect(lambda: self.selected.emit(mode.id))
        layout.addWidget(button)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.mode.id)
        super().mouseReleaseEvent(event)


class ActionSummaryPanel(SectionCard):
    def __init__(self) -> None:
        super().__init__("Shrnutí plánu")
        self.total = QLabel("0 akcí")
        self.admin = QLabel("0 vyžaduje správce")
        self.risky = QLabel("0 rizikových")
        for label in (self.total, self.admin, self.risky):
            label.setObjectName("SummaryNumber")
            self.layout.addWidget(label)

    def set_counts(self, *, total: int, admin: int, risky: int, advanced: int = 0) -> None:
        self.total.setText(f"{total} akcí v plánu")
        self.admin.setText(f"{admin} vyžaduje správce")
        risk_text = f"{risky} rizikových"
        if advanced:
            risk_text += f", {advanced} expert"
        self.risky.setText(risk_text)


class ActionChecklist(QWidget):
    def __init__(
        self,
        actions: Iterable[Action],
        *,
        unchecked_admin_when_not_admin: bool = False,
        default_selected_ids: set[str] | None = None,
    ) -> None:
        super().__init__()
        self.actions = list(actions)
        self._checks: dict[str, QCheckBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        for action in self.actions:
            row = QFrame()
            row.setObjectName("ActionRow")
            row.setMinimumHeight(82)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(16, 12, 16, 12)
            row_layout.setSpacing(14)
            check = QCheckBox()
            if default_selected_ids is None:
                checked = action.default_selected and not action.is_risky_or_expert
            else:
                checked = action.id in default_selected_ids
            if unchecked_admin_when_not_admin and action.requires_admin:
                checked = False
            check.setChecked(checked)
            self._checks[action.id] = check
            check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            text_box = QWidget()
            text_layout = QVBoxLayout(text_box)
            text_layout.setContentsMargins(0, 0, 0, 0)
            text_layout.setSpacing(4)
            title = QLabel(friendly_action_title(action.id))
            title.setObjectName("ActionTitle")
            title.setWordWrap(True)
            description = QLabel(_friendly_description(action))
            description.setObjectName("ActionDescription")
            description.setWordWrap(True)
            text_layout.addWidget(title)
            text_layout.addWidget(description)
            row_layout.addWidget(check)
            row_layout.addWidget(text_box, 1)
            if action.requires_admin:
                row_layout.addWidget(StatusPill("Správce", "warn"))
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
            self._checks[action.id].setChecked(action.risk_level == "safe" and not action.requires_admin)


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
    layout.setSpacing(12)
    for button in buttons:
        layout.addWidget(button)
    layout.addStretch(1)
    return widget


def mode_grid(modes: Iterable[ModeDefinition]) -> QWidget:
    widget = QWidget()
    grid = QGridLayout(widget)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(18)
    for index, mode in enumerate(modes):
        grid.addWidget(ModeCard(mode), index // 2, index % 2)
    return widget


def connect_mode_cards(container: QWidget, callback) -> None:
    for card_widget in container.findChildren(ModeCard):
        card_widget.selected.connect(callback)


def _icon_text(icon: str) -> str:
    return {
        "clean": "✓",
        "speed": "↗",
        "gaming": "▣",
        "work": "▤",
        "repair": "◇",
        "custom": "◎",
        "expert": "!",
    }.get(icon, "•")


def _friendly_description(action: Action) -> str:
    if action.requires_admin:
        return f"{action.description} Vyžaduje spuštění jako správce."
    return action.description
