from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.modules.startup import StartupManager
from app.ui.components import page_header


class StartupPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.manager = StartupManager()
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Name", "Source", "Command", "Publisher", "Recommendation", "Risk"])
        refresh = QPushButton("Refresh Startup Items")
        refresh.clicked.connect(self.populate)
        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Startup Manager", "Review startup entries before disabling anything."))
        layout.addWidget(refresh)
        layout.addWidget(self.table, 1)
        self.populate()

    def populate(self) -> None:
        entries = self.manager.list_entries()
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            values = [entry.name, entry.source, entry.command, entry.publisher, entry.recommendation, entry.risk]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
