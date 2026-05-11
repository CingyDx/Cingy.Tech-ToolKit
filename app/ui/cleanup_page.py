from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import ActionContext
from app.modules.cleanup import get_cleanup_actions
from app.ui.components import ActionChecklist, button_row, page_header
from app.ui.workers import ActionWorker


class CleanupPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.actions = get_cleanup_actions()
        self.checklist = ActionChecklist(self.actions)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self._thread: QThread | None = None
        self._worker: ActionWorker | None = None

        preview = QPushButton("Preview Selected")
        preview.clicked.connect(self.preview_selected)
        execute = QPushButton("Execute Selected")
        execute.clicked.connect(self.execute_selected)
        select_safe = QPushButton("Select Safe")
        select_safe.clicked.connect(self.checklist.select_safe_only)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.checklist.clear_selection)

        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Cleanup", "Safe cleanup targets with estimates before changes."))
        layout.addWidget(button_row(preview, execute, select_safe, clear))
        layout.addWidget(self.checklist)
        layout.addWidget(self.output, 1)

    def _engine(self, dry_run: bool) -> ActionEngine:
        return ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=dry_run))

    def preview_selected(self) -> None:
        actions = self.checklist.selected_actions()
        previews = self._engine(dry_run=True).preview_plan(actions)
        text = []
        for preview in previews:
            text.append(preview.summary)
            text.extend(f"  - {detail}" for detail in preview.details)
            text.extend(f"  ! {warning}" for warning in preview.warnings)
        self.output.setPlainText("\n".join(text) or "No actions selected.")

    def execute_selected(self) -> None:
        actions = self.checklist.selected_actions()
        if not actions:
            self.output.setPlainText("No actions selected.")
            return
        confirmed = QMessageBox.question(
            self,
            "Confirm cleanup",
            f"Execute {len(actions)} selected cleanup action(s)?",
        )
        if confirmed != QMessageBox.Yes:
            return
        self._thread = QThread(self)
        self._worker = ActionWorker(self._engine(dry_run=False), actions, confirmed=True)
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
