from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QLabel, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import ActionContext
from app.modules.expert_lab import ExpertRegistryTweaks
from app.ui.components import ActionChecklist, button_row, page_header, primary_button


class ExpertLabPage(QWidget):
    def __init__(self, enabled_by_config: bool = False) -> None:
        super().__init__()
        self.enabled_by_config = enabled_by_config
        self.ack = QCheckBox("Rozumím, že tato nastavení mohou ovlivnit chování systému")
        self.ack.stateChanged.connect(self._sync_gate)
        self.warning = QLabel("Expert Lab je určený pro technika. Každou změnu nejdřív zobraz v náhledu a vyber ji ručně.")
        self.warning.setObjectName("WarningText")
        self.actions = ExpertRegistryTweaks().actions()
        self.checklist = ActionChecklist(self.actions)
        self.checklist.setEnabled(False)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        preview = primary_button("Náhled vybraných")
        preview.clicked.connect(self.preview)
        self.preview_button = preview

        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Expert Lab", "Pokročilé technické nastavení. Neexistuje zde žádné apply-all tlačítko."))
        layout.addWidget(self.warning)
        layout.addWidget(self.ack)
        layout.addWidget(button_row(preview))
        layout.addWidget(self.checklist)
        layout.addWidget(self.output, 1)
        self._sync_gate()

    def _sync_gate(self) -> None:
        enabled = self.ack.isChecked()
        self.checklist.setEnabled(enabled)
        self.preview_button.setEnabled(enabled)

    def preview(self) -> None:
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=True))
        previews = engine.preview_plan(self.checklist.selected_actions())
        lines = []
        for preview in previews:
            lines.append(preview.summary)
            lines.extend(f"  - {detail}" for detail in preview.details)
            lines.extend(f"  {key}: {value}" for key, value in preview.before_values.items())
        self.output.setPlainText("\n".join(lines) or "No expert tweaks selected.")
