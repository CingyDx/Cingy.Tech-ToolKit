from __future__ import annotations

import json

from PySide6.QtWidgets import QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.core.scanner import SystemScanner
from app.ui.components import page_header


class ScanPage(QWidget):
    def __init__(self, scanner: SystemScanner) -> None:
        super().__init__()
        self.scanner = scanner
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        scan_button = QPushButton("Run System Scan")
        scan_button.clicked.connect(self.run_scan)

        layout = QVBoxLayout(self)
        layout.addWidget(page_header("System Scan", "Collects customer-safe facts used by reports and scoring."))
        layout.addWidget(scan_button)
        layout.addWidget(self.output, 1)

    def run_scan(self) -> None:
        snapshot = self.scanner.scan()
        self.output.setPlainText(json.dumps(snapshot, indent=2, ensure_ascii=False))
