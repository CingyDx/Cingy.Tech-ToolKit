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
from app.core.modes import ModeCatalog
from app.core.scanner import SystemScanner
from app.ui.cleanup_page import CleanupPage
from app.ui.custom_mode_page import CustomModePage
from app.ui.debloat_page import DebloatPage
from app.ui.expert_lab_page import ExpertLabPage
from app.ui.home_page import HomePage
from app.ui.logs_page import LogsPage
from app.ui.modes_page import ModesPage
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
        self.catalog = ModeCatalog.load_default()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 820)
        self.setMinimumSize(1050, 700)
        self.setStyleSheet(STYLE)

        self.nav = QListWidget()
        self.nav.setObjectName("Sidebar")
        self.stack = QStackedWidget()
        self.advanced_button = QPushButton()
        self.advanced_button.setObjectName("AdvancedToggle")
        self.advanced_button.clicked.connect(self._toggle_advanced)

        self.modes_page = ModesPage(self.catalog)
        self.home_page = HomePage(self.scanner, self.config, self.catalog)
        self.home_page.mode_selected.connect(self._open_mode)
        self.home_page.scan_requested.connect(lambda: self._select_page("Kontrola PC"))

        self.default_pages = [
            ("Domů", self.home_page),
            ("Kontrola PC", ScanPage(self.scanner)),
            ("Režimy", self.modes_page),
            ("Reporty", ReportsPage()),
            ("Nastavení", SettingsPage(self.config)),
        ]
        self.advanced_pages = [
            ("Cleanup", CleanupPage()),
            ("Debloat", DebloatPage()),
            ("Startup", StartupPage()),
            ("Power", PowerPage()),
            ("Repair", RepairPage()),
            ("Privacy", PrivacyPage()),
            ("Expert Lab", ExpertLabPage(self.config.enable_expert_lab)),
            ("Custom Mode", CustomModePage()),
            ("Logs", LogsPage()),
        ]
        self._visible_pages: list[tuple[str, QWidget]] = []

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        if not is_running_as_admin():
            root_layout.addWidget(self._admin_banner())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._sidebar(), 0)
        body_layout.addWidget(self.stack, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

        self.nav.currentRowChanged.connect(self._change_page)
        self._rebuild_navigation()
        self._select_page("Domů")

    def _sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("SidebarFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        brand = QFrame()
        brand.setObjectName("SidebarBrand")
        brand_layout = QVBoxLayout(brand)
        title = QLabel(APP_NAME)
        title.setObjectName("SidebarTitle")
        subtitle = QLabel(APP_SUBTITLE)
        subtitle.setObjectName("SidebarSubtitle")
        subtitle.setWordWrap(True)
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        layout.addWidget(brand)
        layout.addWidget(self.nav, 1)
        layout.addWidget(self.advanced_button)
        return frame

    def _rebuild_navigation(self) -> None:
        current_label = self._current_label()
        self.nav.clear()
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)

        self._visible_pages = list(self.default_pages)
        if self.config.show_advanced_tools:
            self._visible_pages.extend(self.advanced_pages)

        for label, widget in self._visible_pages:
            self.nav.addItem(QListWidgetItem(label))
            self.stack.addWidget(widget)

        state = "zapnuto" if self.config.show_advanced_tools else "vypnuto"
        self.advanced_button.setText(f"Technik: {state}")
        self._select_page(current_label if current_label in dict(self._visible_pages) else "Domů")

    def _current_label(self) -> str:
        row = self.nav.currentRow()
        if 0 <= row < len(self._visible_pages):
            return self._visible_pages[row][0]
        return "Domů"

    def _change_page(self, row: int) -> None:
        if 0 <= row < self.stack.count():
            self.stack.setCurrentIndex(row)

    def _select_page(self, label: str) -> None:
        for index, (page_label, _widget) in enumerate(self._visible_pages):
            if page_label == label:
                self.nav.setCurrentRow(index)
                self.stack.setCurrentIndex(index)
                return

    def _open_mode(self, mode_id: str) -> None:
        self.modes_page.show_mode(mode_id)
        self._select_page("Režimy")

    def _toggle_advanced(self) -> None:
        self.config.show_advanced_tools = not self.config.show_advanced_tools
        self.config.save()
        self._rebuild_navigation()

    def _admin_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("AdminBanner")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(18, 10, 18, 10)
        label = QLabel("Některé opravy a optimalizace vyžadují spuštění jako správce.")
        label.setObjectName("BannerText")
        button = QPushButton("Restartovat jako správce")
        button.setObjectName("BannerButton")
        button.clicked.connect(restart_as_admin)
        layout.addWidget(label, 1)
        layout.addWidget(button)
        return banner


STYLE = """
QMainWindow, QWidget {
    background: #111315;
    color: #f4f7fb;
    font-family: Segoe UI, Arial, sans-serif;
    font-size: 12pt;
}
QFrame#SidebarFrame {
    background: #161a1f;
    border-right: 1px solid #2b333c;
    min-width: 245px;
    max-width: 285px;
}
QFrame#SidebarBrand {
    border-bottom: 1px solid #2b333c;
    padding: 8px;
}
QLabel#SidebarTitle {
    font-size: 17pt;
    font-weight: 800;
}
QLabel#SidebarSubtitle {
    color: #8ea0b5;
    font-size: 10.5pt;
}
QListWidget#Sidebar {
    background: transparent;
    border: none;
    outline: none;
    padding: 12px;
}
QListWidget#Sidebar::item {
    padding: 14px 16px;
    margin: 4px 0;
    border-radius: 8px;
    color: #dce7f3;
}
QListWidget#Sidebar::item:selected {
    background: #0e7490;
    color: white;
}
QPushButton#AdvancedToggle {
    margin: 14px;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #3d4855;
    background: #222931;
    color: #b7c7d8;
    font-weight: 700;
}
QFrame#AdminBanner {
    background: #5f3315;
    border-bottom: 1px solid #d78b35;
}
QLabel#BannerText {
    color: #ffddb0;
    font-weight: 700;
}
QPushButton#BannerButton {
    background: #d97706;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    font-weight: 800;
}
QPushButton#PrimaryButton, QPushButton#SecondaryButton, QPushButton#GhostButton, QPushButton {
    border-radius: 8px;
    padding: 12px 18px;
    font-weight: 800;
    min-height: 24px;
}
QPushButton#PrimaryButton, QPushButton {
    background: #0ea5c2;
    border: 1px solid #31d5ee;
    color: #061014;
}
QPushButton#PrimaryButton:hover, QPushButton:hover {
    background: #22d3ee;
}
QPushButton#SecondaryButton {
    background: #232b33;
    border: 1px solid #3e4a56;
    color: #f4f7fb;
}
QPushButton#GhostButton {
    background: transparent;
    border: 1px solid #3e4a56;
    color: #b7c7d8;
}
QPushButton:disabled {
    background: #333a42;
    border-color: #454e58;
    color: #8d99a8;
}
QFrame#SectionCard, QFrame#SectionCardAccent, QFrame#ModeCard, QFrame#ActionRow, QFrame#EmptyState {
    background: #1b2026;
    border: 1px solid #303943;
    border-radius: 8px;
}
QFrame#SectionCardAccent {
    background: #13232a;
    border-color: #0ea5c2;
}
QFrame#ModeCard:hover {
    border-color: #22d3ee;
    background: #202832;
}
QLabel#PageTitle {
    font-size: 30pt;
    font-weight: 900;
    color: #ffffff;
}
QLabel#PageSubtitle, QLabel#MutedText {
    color: #aab8c8;
    font-size: 12pt;
}
QLabel#HeroSubtitle {
    color: #67e8f9;
    font-size: 15pt;
    font-weight: 700;
}
QLabel#CardTitle {
    font-size: 17pt;
    color: #ffffff;
    font-weight: 850;
}
QLabel#ModeTitle {
    font-size: 18pt;
    font-weight: 900;
    color: #ffffff;
}
QLabel#ModeDescription, QLabel#ActionText {
    color: #d9e3ef;
    line-height: 145%;
}
QLabel#ModeIcon {
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
    border-radius: 8px;
    background: #0e7490;
    color: #ffffff;
    font-size: 19pt;
    font-weight: 900;
    qproperty-alignment: AlignCenter;
}
QLabel#RiskBadge, QLabel#StatusPill {
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 10pt;
    font-weight: 900;
}
QLabel#RiskBadge[risk="safe"], QLabel#StatusPill[tone="good"] {
    background: #0f6b4e;
    color: #ddfff3;
}
QLabel#RiskBadge[risk="moderate"], QLabel#StatusPill[tone="warn"] {
    background: #8a5a12;
    color: #fff2cf;
}
QLabel#RiskBadge[risk="risky"] {
    background: #8f2424;
    color: #ffe0e0;
}
QLabel#RiskBadge[risk="expert"] {
    background: #4d2f86;
    color: #efe7ff;
}
QLabel#StatusPill[tone="neutral"] {
    background: #26313c;
    color: #d7e4f0;
}
QLabel#SummaryNumber {
    font-size: 13pt;
    color: #d9e3ef;
}
QLabel#EmptyTitle {
    font-size: 16pt;
    font-weight: 800;
}
QTextEdit, QLineEdit, QTableWidget, QListWidget {
    background: #15191e;
    color: #f4f7fb;
    border: 1px solid #303943;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #0e7490;
}
QTextEdit#TechnicalOutput {
    min-height: 150px;
}
QCheckBox {
    spacing: 10px;
}
QCheckBox::indicator {
    width: 22px;
    height: 22px;
}
QGroupBox#Accordion {
    background: #1b2026;
    border: 1px solid #303943;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    font-size: 14pt;
    font-weight: 850;
}
QGroupBox#Accordion::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
}
QHeaderView::section {
    background: #222931;
    color: #f4f7fb;
    padding: 9px;
    border: 1px solid #303943;
}
QScrollArea {
    border: none;
}
"""
