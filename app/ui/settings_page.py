from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.config import AppConfig
from app.constants import BACKUPS_DIR, LOGS_DIR, REPORTS_DIR
from app.ui.components import SectionCard, make_scroll_area, page_header, primary_button


class SettingsPage(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.technician = QLineEdit(config.technician_name)
        self.language = QComboBox()
        self.language.addItem("Čeština", "cs")
        self.language.addItem("English", "en")
        self.language.setCurrentIndex(0 if config.language == "cs" else 1)
        self.expert = QCheckBox("Povolit Expert Lab")
        self.expert.setChecked(config.enable_expert_lab)
        self.advanced = QCheckBox("Zobrazit technické nástroje v navigaci")
        self.advanced.setChecked(config.show_advanced_tools)
        self.result = QLabel("")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Nastavení", "Lokální nastavení portable aplikace."))
        layout.addWidget(self._general_section())
        layout.addWidget(self._folders_section())
        save = primary_button("Uložit nastavení")
        save.clicked.connect(self.save)
        layout.addWidget(save)
        layout.addWidget(self.result)
        layout.addStretch(1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))

    def _general_section(self) -> QWidget:
        section = SectionCard("Základní")
        form = QFormLayout()
        form.addRow("Technik:", self.technician)
        form.addRow("Jazyk:", self.language)
        form.addRow("Expert Lab:", self.expert)
        form.addRow("Technické nástroje:", self.advanced)
        section.layout.addLayout(form)
        return section

    def _folders_section(self) -> QWidget:
        section = SectionCard("Lokální složky")
        for label, path in (
            ("Logy", LOGS_DIR),
            ("Reporty", REPORTS_DIR),
            ("Zálohy", BACKUPS_DIR),
        ):
            section.layout.addWidget(QLabel(f"{label}: {path}"))
        return section

    def save(self) -> None:
        self.config.technician_name = self.technician.text().strip() or self.config.technician_name
        self.config.language = str(self.language.currentData())
        self.config.enable_expert_lab = self.expert.isChecked()
        self.config.show_advanced_tools = self.advanced.isChecked()
        self.config.save()
        self.result.setText("Nastavení uloženo. Navigace se aktualizuje po restartu nebo tlačítkem Technik vlevo.")
