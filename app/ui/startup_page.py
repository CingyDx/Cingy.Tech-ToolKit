from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.modules.startup import StartupManager
from app.ui.components import SectionCard, StatusPill, button_row, make_scroll_area, page_header, primary_button, secondary_button


class StartupPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.manager = StartupManager()
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Název", "Zdroj", "Příkaz", "Vydavatel", "Doporučení", "Riziko"])
        self.table.hide()
        self.summary = QLabel("Nejdřív obnov seznam aplikací po startu.")
        self.summary.setWordWrap(True)

        refresh = primary_button("Obnovit aplikace po startu")
        refresh.clicked.connect(self.populate)
        toggle = secondary_button("Zobrazit detailní seznam")
        toggle.clicked.connect(self.toggle_table)
        self.toggle = toggle

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Startup", "Aplikace spouštěné po startu Windows. Vypnutí se v MVP nespouští automaticky."))
        card = SectionCard("Přehled po startu")
        card.layout.addWidget(self.summary)
        card.layout.addWidget(StatusPill("Technické detaily jsou skryté", "neutral"))
        layout.addWidget(card)
        layout.addWidget(button_row(refresh, toggle))
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
        entries = self.manager.list_entries()
        self.summary.setText(f"Nalezeno {len(entries)} položek po startu. Doporučení k vypnutí se zobrazí v detailu.")
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            values = [entry.name, entry.source, entry.command, entry.publisher, entry.recommendation, entry.risk]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
