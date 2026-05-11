from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.modules.startup import StartupEntry, StartupManager
from app.ui.components import SectionCard, StatusPill, button_row, make_scroll_area, page_header, primary_button, secondary_button


class StartupPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.manager = StartupManager()
        self.entries: list[StartupEntry] = []
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Název", "Stav", "Zdroj", "Příkaz", "Vydavatel", "Doporučení", "Riziko", "Možnost"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.hide()
        self.summary = QLabel("Nejdřív obnov seznam aplikací po startu.")
        self.summary.setWordWrap(True)
        self.output = QLabel("Nic se nevypne bez výběru položky a potvrzení.")
        self.output.setWordWrap(True)
        self.output.setObjectName("MutedText")

        refresh = primary_button("Obnovit aplikace po startu")
        refresh.clicked.connect(self.populate)
        toggle = secondary_button("Zobrazit detailní seznam")
        toggle.clicked.connect(self.toggle_table)
        self.toggle = toggle
        disable = primary_button("Vypnout vybranou položku")
        disable.clicked.connect(self.disable_selected)
        enable = secondary_button("Obnovit vypnutou položku")
        enable.clicked.connect(self.enable_selected)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Startup", "Aplikace spouštěné po startu Windows. Vypnutí je ruční, zálohované a jen pro podporované položky."))
        card = SectionCard("Přehled po startu")
        card.layout.addWidget(self.summary)
        card.layout.addWidget(StatusPill("Technické detaily jsou skryté", "neutral"))
        card.layout.addWidget(self.output)
        layout.addWidget(card)
        layout.addWidget(button_row(refresh, toggle, disable, enable))
        layout.addWidget(self.table, 1)
        layout.addStretch(1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))
        self.populate()

    def toggle_table(self) -> None:
        visible = not self.table.isVisible()
        self.table.setVisible(visible)
        self.toggle.setText("Skrýt detailní seznam" if visible else "Zobrazit detailní seznam")

    def populate(self) -> None:
        self.entries = self.manager.list_entries()
        disable_count = sum(1 for entry in self.entries if entry.can_disable)
        disabled_count = sum(1 for entry in self.entries if not entry.enabled)
        self.summary.setText(
            f"Nalezeno {len(self.entries)} položek po startu. "
            f"Bezpečně vypnout lze {disable_count} uživatelských položek; vypnutých ToolKitem je {disabled_count}."
        )
        self.table.setRowCount(len(self.entries))
        for row, entry in enumerate(self.entries):
            values = [
                entry.name,
                "Zapnuto" if entry.enabled else "Vypnuto",
                entry.source,
                entry.command,
                entry.publisher,
                entry.recommendation,
                entry.risk,
                _capability_text(entry),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()

    def disable_selected(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self.output.setText("Vyber položku v detailním seznamu.")
            return
        if not entry.can_disable:
            self.output.setText("Tahle položka se v MVP bezpečně nevypíná. Podporované jsou zatím uživatelské položky HKCU Run.")
            return
        confirmed = QMessageBox.question(
            self,
            "Potvrdit vypnutí startup položky",
            f"Vypnout po startu položku „{entry.name}“? Původní hodnota se uloží do backups/startup_disabled.json.",
        )
        if confirmed != QMessageBox.Yes:
            return
        try:
            self.output.setText(self.manager.disable_entry(entry.id))
        except Exception as exc:
            self.output.setText(str(exc))
            return
        self.populate()

    def enable_selected(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self.output.setText("Vyber vypnutou položku v detailním seznamu.")
            return
        if not entry.can_enable:
            self.output.setText("Tahle položka nemá zálohu vytvořenou ToolKitem.")
            return
        try:
            self.output.setText(self.manager.enable_entry(entry.id))
        except Exception as exc:
            self.output.setText(str(exc))
            return
        self.populate()

    def _selected_entry(self) -> StartupEntry | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.entries):
            return None
        return self.entries[row]


def _capability_text(entry: StartupEntry) -> str:
    if entry.can_disable:
        return "Lze vypnout"
    if entry.can_enable:
        return "Lze obnovit"
    return "Pouze přehled"
