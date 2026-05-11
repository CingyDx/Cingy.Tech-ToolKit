from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import ActionContext
from app.modules.repair import get_repair_actions
from app.ui.components import ActionChecklist, button_row, page_header
from app.ui.workers import ActionWorker


class RepairPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.actions = get_repair_actions()
        self.checklist = ActionChecklist(self.actions)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self._thread: QThread | None = None
        self._worker: ActionWorker | None = None

        preview = QPushButton("Preview")
        preview.clicked.connect(self.preview)
        run = QPushButton("Execute Selected")
        run.clicked.connect(self.execute)
        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Repair Tools", "Technician repair commands with output capture."))
        layout.addWidget(button_row(preview, run))
        layout.addWidget(self.checklist)
        layout.addWidget(self.output, 1)

    def preview(self) -> None:
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=True))
        previews = engine.preview_plan(self.checklist.selected_actions())
        lines = []
        for preview in previews:
            lines.append(preview.summary)
            lines.extend(f"  - {detail}" for detail in preview.details)
            lines.extend(f"  ! {warning}" for warning in preview.warnings)
        self.output.setPlainText("\n".join(lines) or "No actions selected.")

    def execute(self) -> None:
        actions = self.checklist.selected_actions()
        if not actions:
            self.output.setPlainText("No actions selected.")
            return
        confirmed = QMessageBox.question(self, "Confirm repair", f"Run {len(actions)} repair action(s)?")
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
