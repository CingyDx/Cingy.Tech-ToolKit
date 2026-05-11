from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget

from app.core.scanner import SystemScanner
from app.ui.components import card, page_header


class DashboardPage(QWidget):
    def __init__(self, scanner: SystemScanner) -> None:
        super().__init__()
        self.scanner = scanner
        self.cards = QGridLayout()
        self.details = QTextEdit()
        self.details.setReadOnly(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(page_header("Dashboard", "Service overview and transparent system health score."))
        refresh = QPushButton("Refresh Scan")
        refresh.clicked.connect(self.refresh)
        layout.addWidget(refresh)
        layout.addLayout(self.cards)
        layout.addWidget(self.details)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.addWidget(scroll)
        self.refresh()

    def refresh(self) -> None:
        snapshot = self.scanner.scan()
        while self.cards.count():
            item = self.cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        rows = [
            ("Windows", snapshot.get("windows_version", "Unknown")),
            ("Device", snapshot.get("device_name", "Unknown")),
            ("CPU", snapshot.get("cpu", "Unknown")),
            ("RAM", f"{snapshot.get('ram_total_gb', 0)} GB, {snapshot.get('ram_used_percent', 0)}% used"),
            ("GPU", snapshot.get("gpu", "Unknown")),
            ("Apps", str(snapshot.get("installed_app_count", 0))),
            ("Startup", str(snapshot.get("startup_item_count", 0))),
            ("Bloatware", str(snapshot.get("detected_bloatware_count", 0))),
            ("Temp/cache", f"{int(snapshot.get('temp_cache_estimated_bytes', 0)) / (1024**3):.1f} GB"),
            ("Admin", "Yes" if snapshot.get("admin_status") else "No"),
            ("Health", f"{snapshot.get('health_score', 0)}/100"),
            ("Last scan", snapshot.get("last_scan_time", "Never")),
        ]
        for index, (title, body) in enumerate(rows):
            self.cards.addWidget(card(title, str(body)), index // 3, index % 3)
        explanations = "\n".join(f"- {item}" for item in snapshot.get("health_explanations", []))
        disks = "\n".join(
            f"- {disk.get('mountpoint')}: {disk.get('used_percent')}% used, {disk.get('free_gb')} GB free"
            for disk in snapshot.get("disks", [])
        )
        self.details.setPlainText(
            "Score explanation:\n"
            f"{explanations}\n\n"
            "Disk list:\n"
            f"{disks or '- No disks detected'}\n\n"
            f"Activation: {snapshot.get('windows_activation_status')}\n"
            f"Windows Update: {snapshot.get('windows_update_status')}"
        )
