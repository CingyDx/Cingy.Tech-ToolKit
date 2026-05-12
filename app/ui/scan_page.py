from __future__ import annotations

import json

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from app.core.scanner import SystemScanner
from app.ui.components import SectionCard, StatusPill, make_scroll_area, page_header, primary_button, secondary_button


class ScanPage(QWidget):
    def __init__(self, scanner: SystemScanner) -> None:
        super().__init__()
        self.scanner = scanner
        self.summary = SectionCard("Stav počítače", "Nejdřív spusť kontrolu PC.")
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.hide()
        self.details_visible = False

        scan_button = primary_button("Spustit kontrolu")
        scan_button.clicked.connect(self.run_scan)
        details_button = secondary_button("Zobrazit technické detaily")
        details_button.clicked.connect(self.toggle_details)
        self.details_button = details_button

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Kontrola PC", "Rychlá kontrola zjistí stav počítače bez provádění změn."))
        layout.addWidget(self.summary)
        layout.addWidget(scan_button)
        layout.addWidget(details_button)
        layout.addWidget(self.details, 1)
        layout.addStretch(1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))

    def run_scan(self) -> None:
        snapshot = self.scanner.scan()
        self._set_summary(snapshot)
        self.details.setPlainText(json.dumps(snapshot, indent=2, ensure_ascii=False))

    def toggle_details(self) -> None:
        self.details_visible = not self.details_visible
        self.details.setVisible(self.details_visible)
        self.details_button.setText("Skrýt technické detaily" if self.details_visible else "Zobrazit technické detaily")

    def _set_summary(self, snapshot: dict[str, object]) -> None:
        while self.summary.layout.count() > 2:
            item = self.summary.layout.takeAt(2)
            if item.widget():
                item.widget().deleteLater()
        score = snapshot.get("health_score", "?")
        temp_gb = int(snapshot.get("temp_cache_estimated_bytes", 0)) / (1024**3)
        self.summary.layout.addWidget(StatusPill(f"Skóre stavu: {score}/100", "good"))
        self.summary.layout.addWidget(QLabel(f"Zařízení: {snapshot.get('device_name', 'Neznámé')}"))
        self.summary.layout.addWidget(QLabel(f"Windows: {snapshot.get('windows_version', 'Neznámé')}"))
        self.summary.layout.addWidget(QLabel(f"RAM: {snapshot.get('ram_total_gb', '?')} GB, využití {snapshot.get('ram_used_percent', '?')}%"))
        self.summary.layout.addWidget(QLabel(f"GPU: {snapshot.get('gpu', 'Neznámé')}"))
        self.summary.layout.addWidget(QLabel(f"Typ disku: {snapshot.get('boot_drive_type', 'unknown')}"))
        self.summary.layout.addWidget(QLabel(f"Aktivace Windows: {snapshot.get('windows_activation_status', 'Neznámé')}"))
        self.summary.layout.addWidget(QLabel(f"Windows Update: {snapshot.get('windows_update_status', 'Neznámé')}"))
        self.summary.layout.addWidget(QLabel(f"Aplikace po startu: {snapshot.get('startup_item_count', 0)}"))
        self.summary.layout.addWidget(QLabel(f"Odhad dočasných souborů: {temp_gb:.1f} GB"))
