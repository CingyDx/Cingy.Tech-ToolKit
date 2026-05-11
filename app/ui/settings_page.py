from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.config import AppConfig
from app.ui.components import page_header


class SettingsPage(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.technician = QLineEdit(config.technician_name)
        self.expert = QCheckBox("Enable Expert Lab")
        self.expert.setChecked(config.enable_expert_lab)
        save = QPushButton("Save Settings")
        save.clicked.connect(self.save)
        form = QFormLayout()
        form.addRow("Technician:", self.technician)
        form.addRow("Expert Lab:", self.expert)

        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Settings", "Local portable-mode settings."))
        layout.addLayout(form)
        layout.addWidget(save)
        layout.addStretch(1)

    def save(self) -> None:
        self.config.technician_name = self.technician.text().strip() or self.config.technician_name
        self.config.enable_expert_lab = self.expert.isChecked()
        self.config.save()
