from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.admin import is_running_as_admin, restart_as_admin
from app.config import AppConfig
from app.constants import APP_NAME, APP_SUBTITLE
from app.core.scanner import SystemScanner
from app.ui.cleanup_page import CleanupPage
from app.ui.custom_mode_page import CustomModePage
from app.ui.dashboard_page import DashboardPage
from app.ui.debloat_page import DebloatPage
from app.ui.expert_lab_page import ExpertLabPage
from app.ui.power_page import PowerPage
from app.ui.privacy_page import PrivacyPage
from app.ui.repair_page import RepairPage
from app.ui.reports_page import ReportsPage
from app.ui.scan_page import ScanPage
from app.ui.settings_page import SettingsPage
from app.ui.startup_page import StartupPage


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig | None = None) -> None:
        super().__init__()
        self.config = config or AppConfig.load()
        self.scanner = SystemScanner()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 820)
        self.setStyleSheet(STYLE)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)

        if not is_running_as_admin():
            root_layout.addWidget(self._admin_banner())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        self.nav = QListWidget()
        self.nav.setObjectName("Sidebar")
        self.stack = QStackedWidget()
        self.pages = [
            ("Dashboard", DashboardPage(self.scanner)),
            ("System Scan", ScanPage(self.scanner)),
            ("Cleanup", CleanupPage()),
            ("Debloat", DebloatPage()),
            ("Startup Manager", StartupPage()),
            ("Power & Performance", PowerPage()),
            ("Repair Tools", RepairPage()),
            ("Privacy & Settings", PrivacyPage()),
            ("Expert Lab", ExpertLabPage(self.config.enable_expert_lab)),
            ("Custom Mode", CustomModePage()),
            ("Reports", ReportsPage()),
            ("Settings", SettingsPage(self.config)),
        ]
        self._build_sidebar()
        body_layout.addWidget(self.nav, 0)
        body_layout.addWidget(self.stack, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)

    def _build_sidebar(self) -> None:
        for title, page in self.pages:
            self.nav.addItem(QListWidgetItem(title))
            self.stack.addWidget(page)

    def _admin_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("AdminBanner")
        layout = QHBoxLayout(banner)
        label = QLabel("Some repair and optimization actions require Administrator access.")
        button = QPushButton("Restart as Administrator")
        button.clicked.connect(restart_as_admin)
        layout.addWidget(label, 1)
        layout.addWidget(button)
        return banner


STYLE = """
QMainWindow, QWidget {
    background: #111827;
    color: #e5e7eb;
    font-family: Segoe UI, Arial, sans-serif;
    font-size: 10.5pt;
}
QListWidget#Sidebar {
    background: #0b1220;
    border: none;
    min-width: 230px;
    max-width: 260px;
}
QListWidget#Sidebar::item {
    padding: 12px 16px;
    border-bottom: 1px solid #162033;
}
QListWidget#Sidebar::item:selected {
    background: #0e7490;
}
QFrame#AdminBanner {
    background: #7c2d12;
    border-bottom: 1px solid #fed7aa;
}
QPushButton {
    background: #0891b2;
    border: 1px solid #22d3ee;
    border-radius: 6px;
    padding: 8px 12px;
    color: white;
    font-weight: 600;
}
QPushButton:hover {
    background: #0e7490;
}
QPushButton:disabled {
    background: #374151;
    border-color: #4b5563;
    color: #9ca3af;
}
QFrame#Card, QFrame#ActionRow {
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 8px;
}
QLabel#PageTitle {
    font-size: 22pt;
    font-weight: 700;
}
QLabel#CardTitle {
    color: #67e8f9;
    font-weight: 700;
}
QLabel#MutedText {
    color: #9ca3af;
}
QLabel#WarningText {
    color: #fcd34d;
    font-weight: 700;
}
QLabel#RiskBadge {
    min-width: 78px;
    max-width: 78px;
    border-radius: 4px;
    padding: 4px;
    font-size: 8.5pt;
}
QLabel#RiskBadge[risk="safe"] { background: #065f46; }
QLabel#RiskBadge[risk="moderate"] { background: #92400e; }
QLabel#RiskBadge[risk="risky"] { background: #991b1b; }
QLabel#RiskBadge[risk="expert"] { background: #581c87; }
QTextEdit, QLineEdit, QTableWidget, QListWidget {
    background: #0f172a;
    color: #e5e7eb;
    border: 1px solid #374151;
    border-radius: 6px;
}
QHeaderView::section {
    background: #1f2937;
    color: #e5e7eb;
    padding: 6px;
    border: 1px solid #374151;
}
"""
