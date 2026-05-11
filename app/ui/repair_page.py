from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import Action, ActionContext
from app.core.modes import friendly_action_title
from app.modules.repair import get_repair_actions
from app.ui.components import ActionChecklist, SectionCard, button_row, make_scroll_area, page_header, primary_button
from app.ui.workers import ActionWorker


class RepairPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.actions = get_repair_actions()
        self.group_checklists: list[ActionChecklist] = []
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self._thread: QThread | None = None
        self._worker: ActionWorker | None = None

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Repair", "Servisní opravy Windows. Některé akce trvají dlouho a mohou vyžadovat restart."))
        for title, body, ids in self._groups():
            card = SectionCard(title, body)
            actions = [action for action in self.actions if action.id in ids]
            checklist = ActionChecklist(actions, unchecked_admin_when_not_admin=not is_running_as_admin())
            self.group_checklists.append(checklist)
            card.layout.addWidget(checklist)
            layout.addWidget(card)
        preview = primary_button("Náhled oprav")
        preview.clicked.connect(self.preview)
        run = primary_button("Spustit vybrané opravy")
        run.clicked.connect(self.execute)
        layout.addWidget(button_row(preview, run))
        layout.addWidget(self.output, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))

    def selected_actions(self) -> list[Action]:
        selected: list[Action] = []
        for checklist in self.group_checklists:
            selected.extend(checklist.selected_actions())
        return selected

    def preview(self) -> None:
        actions = self.selected_actions()
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné opravy.")
            return
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=True))
        previews = engine.preview_plan(actions)
        lines = ["Náhled oprav:"]
        for preview in previews:
            lines.append(f"- {friendly_action_title(preview.action_id)}: {preview.summary}")
            for warning in preview.warnings:
                lines.append(f"  Pozor: {warning}")
        self.output.setPlainText("\n".join(lines))

    def execute(self) -> None:
        actions = self.selected_actions()
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné opravy.")
            return
        confirmed = QMessageBox.question(self, "Potvrdit opravy", f"Spustit {len(actions)} vybraných oprav?")
        if confirmed != QMessageBox.Yes:
            return
        self._thread = QThread(self)
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=False))
        self._worker = ActionWorker(engine, actions, confirmed=True)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.start()

    def _on_finished(self, results: list) -> None:
        self.output.setPlainText("\n".join(f"{result.message}\n{result.stdout[:1000]}" for result in results))

    def _on_failed(self, message: str) -> None:
        self.output.setPlainText(message)

    def _groups(self) -> list[tuple[str, str, set[str]]]:
        return [
            (
                "Oprava systémových souborů",
                "Může pomoct při chybách Windows. Obvykle trvá několik minut.",
                {"repair.sfc_scan"},
            ),
            (
                "Oprava obrazu Windows",
                "Kontrola a oprava systémového obrazu. RestoreHealth může trvat déle.",
                {"repair.dism_checkhealth", "repair.dism_scanhealth", "repair.dism_restorehealth"},
            ),
            (
                "Kontrola disku",
                "Read-only kontrola disku bez mazání souborů.",
                {"repair.chkdsk_scan"},
            ),
            (
                "Oprava internetu / sítě",
                "DNS a síťové reset kroky. Restart může být potřeba.",
                {"repair.flush_dns", "repair.winsock_reset", "repair.ip_stack_reset"},
            ),
        ]
