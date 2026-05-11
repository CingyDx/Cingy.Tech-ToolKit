from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.modules.debloat import BloatwareManager
from app.ui.components import SectionCard, StatusPill, button_row, make_scroll_area, page_header, primary_button, secondary_button


class DebloatPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.manager = BloatwareManager()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtrovat aplikace")
        self.search.textChanged.connect(self.populate)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Aplikace", "Vydavatel", "Typ", "Riziko", "Důvod", "Metoda"])
        self.table.hide()
        self.summary = QLabel("Nejdřív spusť detekci.")
        self.summary.setWordWrap(True)

        refresh = primary_button("Najít zbytečné aplikace")
        refresh.clicked.connect(self.populate)
        toggle = secondary_button("Zobrazit detailní seznam")
        toggle.clicked.connect(self.toggle_table)
        self.toggle = toggle

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Debloat", "Předinstalované a zkušební aplikace. Nic nebude odstraněno bez potvrzení."))
        intro = SectionCard("Nalezené zbytečné aplikace")
        intro.layout.addWidget(self.summary)
        intro.layout.addWidget(StatusPill("Nic nebude odstraněno bez potvrzení", "good"))
        layout.addWidget(intro)
        layout.addWidget(button_row(refresh, toggle))
        layout.addWidget(self.search)
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
        detected = self.manager.detect()
        query = self.search.text().lower()
        if query:
            detected = [item for item in detected if query in item.name.lower()]
        self.summary.setText(
            f"Nalezeno {len(detected)} položek k ruční kontrole. Doporučené odstranění vždy potvrzuje technik."
            if detected
            else "Zatím nebyly nalezené žádné položky podle pravidel MVP."
        )
        self.table.setRowCount(len(detected))
        for row, item in enumerate(detected):
            values = [item.name, item.publisher, item.app_type, item.risk, item.reason, item.uninstall_method]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
