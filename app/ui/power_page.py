from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMessageBox, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import ActionContext
from app.modules.power import PowerManager
from app.ui.components import ActionChecklist, SectionCard, button_row, page_header, primary_button, secondary_button


class PowerPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.manager = PowerManager()
        self.actions = []
        self.checklist: ActionChecklist | None = None
        self.plan_status = QLabel("Načítám režimy napájení z Windows...")
        self.plan_status.setWordWrap(True)
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        preview = primary_button("Náhled")
        preview.clicked.connect(self.preview)
        run = primary_button("Spustit vybrané")
        run.clicked.connect(self.execute)
        refresh = secondary_button("Obnovit režimy napájení")
        refresh.clicked.connect(self.refresh_actions)

        self.action_holder = QWidget()
        self.action_layout = QVBoxLayout(self.action_holder)
        self.action_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Napájení a výkon", "Zobrazí režimy napájení přímo z Windows a dovolí ruční přepnutí po potvrzení."))
        status_card = SectionCard("Aktuální stav")
        status_card.layout.addWidget(self.plan_status)
        layout.addWidget(status_card)
        layout.addWidget(button_row(refresh, preview, run))
        layout.addWidget(self.action_holder)
        layout.addWidget(self.output, 1)
        self.refresh_actions()

    def refresh_actions(self) -> None:
        plans = self.manager.list_power_plans()
        active_plan = next((plan for plan in plans if plan.is_active), None)
        if active_plan:
            self.plan_status.setText(f"Aktuální režim napájení: {active_plan.name}")
        elif plans:
            self.plan_status.setText("Windows vrátil seznam režimů, ale aktivní režim nebyl označen.")
        else:
            self.plan_status.setText("Nepodařilo se načíst seznam režimů napájení. Kontrolu aktuálního režimu lze zkusit samostatně.")

        actions = [self.manager.current_plan_preview_action()]
        for plan in plans:
            if plan.is_active:
                continue
            actions.append(self.manager.switch_plan_action(plan.guid, plan.name))
        self.actions = actions
        self._replace_checklist(ActionChecklist(self.actions, default_selected_ids={"power.current_plan"}))

    def preview(self) -> None:
        if self.checklist is None:
            self.output.setPlainText("Nejdřív obnov seznam režimů napájení.")
            return
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=True))
        previews = engine.preview_plan(self.checklist.selected_actions())
        lines: list[str] = []
        for preview in previews:
            lines.append(f"- {preview.summary}")
            lines.extend(f"  Pozor: {warning}" for warning in preview.warnings)
        self.output.setPlainText("\n".join(lines) or "Zatím nebyly vybrané žádné akce.")

    def execute(self) -> None:
        if self.checklist is None:
            self.output.setPlainText("Nejdřív obnov seznam režimů napájení.")
            return
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
        lines: list[str] = []
        for result in results:
            lines.append(f"- {result.message}")
            stdout = result.stdout.strip()
            if stdout:
                lines.append(f"  Detail: {stdout[:500]}")
        self.output.setPlainText("\n".join(lines))
        self.refresh_actions()

    def _replace_checklist(self, checklist: ActionChecklist) -> None:
        while self.action_layout.count():
            item = self.action_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.checklist = checklist
        self.action_layout.addWidget(checklist)
