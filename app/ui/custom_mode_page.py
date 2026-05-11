from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QGroupBox, QLabel, QMessageBox, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import Action, ActionContext
from app.core.report_generator import ReportGenerator
from app.core.restore_point import create_restore_point_action
from app.modules.cleanup import get_cleanup_actions
from app.modules.repair import get_repair_actions
from app.ui.components import ActionChecklist, SectionCard, button_row, make_scroll_area, page_header, primary_button, secondary_button
from app.ui.workers import ActionWorker


class CustomModePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.actions = [create_restore_point_action(), *get_cleanup_actions(), *get_repair_actions()]
        self.group_checklists: list[ActionChecklist] = []
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self._thread: QThread | None = None
        self._worker: ActionWorker | None = None
        self.count_label = QLabel("Vybrané akce: 0")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Custom Mode", "Pohodlný ruční stavitel servisního plánu."))
        layout.addWidget(SectionCard("Pravidlo bezpečnosti", "Nejdřív náhled plánu. Spustí se pouze vybrané akce."))
        for title, actions, expanded in self._groups():
            box = QGroupBox(title)
            box.setObjectName("Accordion")
            box.setCheckable(True)
            box.setChecked(expanded)
            box_layout = QVBoxLayout(box)
            checklist = ActionChecklist(actions, unchecked_admin_when_not_admin=not is_running_as_admin())
            checklist.setVisible(expanded)
            box.toggled.connect(checklist.setVisible)
            self.group_checklists.append(checklist)
            box_layout.addWidget(checklist)
            layout.addWidget(box)
        preview = primary_button("Náhled plánu")
        preview.clicked.connect(self.preview)
        restore = secondary_button("Vytvořit bod obnovení")
        restore.clicked.connect(self.create_restore_point)
        execute = primary_button("Spustit vybrané")
        execute.clicked.connect(self.execute)
        report = secondary_button("Vygenerovat report")
        report.clicked.connect(self.generate_report)
        layout.addWidget(self.count_label)
        layout.addWidget(button_row(preview, restore, execute, report))
        layout.addWidget(self.output, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))

    def selected_actions(self) -> list[Action]:
        selected: list[Action] = []
        for checklist in self.group_checklists:
            selected.extend(checklist.selected_actions())
        self.count_label.setText(f"Vybrané akce: {len(selected)}")
        return selected

    def preview(self) -> None:
        actions = self.selected_actions()
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné akce.")
            return
        previews = self._engine(True).preview_plan(actions)
        lines = ["Plán akce:"]
        lines.extend(f"{index}. {preview.summary}" for index, preview in enumerate(previews, 1))
        self.output.setPlainText("\n".join(lines))

    def create_restore_point(self) -> None:
        self._run_actions([create_restore_point_action()])

    def execute(self) -> None:
        self._run_actions(self.selected_actions())

    def generate_report(self) -> None:
        path = ReportGenerator().generate(raw_logs=self.output.toPlainText())
        self.output.setPlainText(f"Report generated: {path}")

    def _engine(self, dry_run: bool) -> ActionEngine:
        return ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=dry_run))

    def _run_actions(self, actions: list[Action]) -> None:
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné akce.")
            return
        confirmed = QMessageBox.question(self, "Potvrdit spuštění", f"Spustit {len(actions)} vybraných akcí?")
        if confirmed != QMessageBox.Yes:
            return
        self._thread = QThread(self)
        self._worker = ActionWorker(self._engine(False), actions, confirmed=True)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.start()

    def _on_finished(self, results: list) -> None:
        self.output.setPlainText("\n".join(result.message for result in results))

    def _on_failed(self, message: str) -> None:
        self.output.setPlainText(message)

    def _groups(self) -> list[tuple[str, list[Action], bool]]:
        safe = [action for action in self.actions if action.risk_level == "safe" and not action.requires_admin]
        optional = [action for action in self.actions if action.risk_level == "moderate" and not action.requires_admin]
        admin = [action for action in self.actions if action.requires_admin and action.risk_level != "expert"]
        risky = [action for action in self.actions if action.risk_level in {"risky", "expert"}]
        return [
            ("Bezpečné", safe, True),
            ("Volitelné", optional, True),
            ("Vyžaduje správce", admin, False),
            ("Pokročilé / rizikové", risky, False),
        ]
