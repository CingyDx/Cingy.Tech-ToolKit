from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.modules.debloat import BloatwareManager
from app.ui.components import page_header


class DebloatPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.manager = BloatwareManager()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter apps")
        self.search.textChanged.connect(self.populate)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["App", "Publisher", "Type", "Risk", "Reason", "Method"])

        refresh = QPushButton("Detect Bloatware")
        refresh.clicked.connect(self.populate)
        safe = QPushButton("Select safe bloatware only")
        oem = QPushButton("Select OEM trialware")
        clear = QPushButton("Clear selection")
        buttons = QWidget()
        row = QHBoxLayout(buttons)
        for button in (refresh, safe, oem, clear):
            row.addWidget(button)
        row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Debloat", "Manual bloatware review. Nothing is removed automatically."))
        layout.addWidget(self.search)
        layout.addWidget(buttons)
        layout.addWidget(self.table, 1)
        self.populate()

    def populate(self) -> None:
        detected = self.manager.detect()
        query = self.search.text().lower()
        if query:
            detected = [item for item in detected if query in item.name.lower()]
        self.table.setRowCount(len(detected))
        for row, item in enumerate(detected):
            values = [item.name, item.publisher, item.app_type, item.risk, item.reason, item.uninstall_method]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
