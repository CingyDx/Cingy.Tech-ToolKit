from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.modules.privacy import load_privacy_toggles
from app.ui.components import page_header


class PrivacyPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Setting", "Risk", "Admin", "Explanation"])
        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Privacy & Windows Settings", "Safe user-facing toggles with clear descriptions."))
        layout.addWidget(self.table, 1)
        self.populate()

    def populate(self) -> None:
        toggles = load_privacy_toggles()
        self.table.setRowCount(len(toggles))
        for row, toggle in enumerate(toggles):
            values = [
                toggle.get("title", ""),
                toggle.get("risk", ""),
                "Yes" if toggle.get("requires_admin") else "No",
                toggle.get("description", ""),
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
