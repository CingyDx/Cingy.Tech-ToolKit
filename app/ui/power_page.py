from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.constants import RULES_DIR
from app.core.action_engine import ActionEngine
from app.core.action_model import ActionContext
from app.core.state_store import JsonRuleStore
from app.modules.power import PowerManager
from app.ui.components import ActionChecklist, button_row, page_header


class PowerPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.manager = PowerManager()
        self.actions = [self.manager.current_plan_preview_action()]
        for profile in JsonRuleStore(RULES_DIR).load_required("power_profiles.json").get("profiles", []):
            self.actions.append(
                self.manager.switch_plan_action(
                    str(profile["powercfg_alias"]),
                    str(profile["name"]),
                    str(profile["risk"]),
                )
            )
        self.checklist = ActionChecklist(self.actions)
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        preview = QPushButton("Preview")
        preview.clicked.connect(self.preview)
        run = QPushButton("Execute Selected")
        run.clicked.connect(self.execute)

        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Power & Performance", "Power plan review and manual switching."))
        layout.addWidget(button_row(preview, run))
        layout.addWidget(self.checklist)
        layout.addWidget(self.output, 1)

    def preview(self) -> None:
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=True))
        previews = engine.preview_plan(self.checklist.selected_actions())
        self.output.setPlainText("\n".join(preview.summary for preview in previews) or "No actions selected.")

    def execute(self) -> None:
        actions = self.checklist.selected_actions()
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné akce.")
            return
        confirmed = QMessageBox.question(self, "Potvrdit změnu napájení", f"Spustit {len(actions)} vybraných akcí?")
        if confirmed != QMessageBox.Yes:
            return
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=False))
        try:
            results = engine.execute_plan(actions, confirmed=True)
        except Exception as exc:
            self.output.setPlainText(str(exc))
            return
        self.output.setPlainText("\n".join(result.message for result in results))
