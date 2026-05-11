from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import ActionContext
from app.core.report_generator import ReportGenerator
from app.core.restore_point import create_restore_point_action
from app.modules.cleanup import get_cleanup_actions
from app.modules.repair import get_repair_actions
from app.ui.components import ActionChecklist, button_row, page_header
from app.ui.workers import ActionWorker


class CustomModePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.actions = [create_restore_point_action(), *get_cleanup_actions(), *get_repair_actions()]
        self.checklist = ActionChecklist(self.actions)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self._thread: QThread | None = None
        self._worker: ActionWorker | None = None
        preview = QPushButton("Preview Plan")
        preview.clicked.connect(self.preview)
        restore = QPushButton("Create Restore Point")
        restore.clicked.connect(self.create_restore_point)
        execute = QPushButton("Execute Selected")
        execute.clicked.connect(self.execute)
        report = QPushButton("Generate Report")
        report.clicked.connect(self.generate_report)

        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Custom Mode", "Build a manual action plan from safe toolkit actions."))
        layout.addWidget(button_row(preview, restore, execute, report))
        layout.addWidget(self.checklist)
        layout.addWidget(self.output, 1)

    def _engine(self, dry_run: bool) -> ActionEngine:
        return ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=dry_run))

    def preview(self) -> None:
        previews = self._engine(True).preview_plan(self.checklist.selected_actions())
        lines = ["Plán akce:"]
        lines.extend(f"{index}. {preview.summary}" for index, preview in enumerate(previews, 1))
        self.output.setPlainText("\n".join(lines))

    def create_restore_point(self) -> None:
        self._run_actions([create_restore_point_action()])

    def execute(self) -> None:
        self._run_actions(self.checklist.selected_actions())

    def generate_report(self) -> None:
        path = ReportGenerator().generate(raw_logs=self.output.toPlainText())
        self.output.setPlainText(f"Report generated: {path}")

    def _run_actions(self, actions) -> None:
        if not actions:
            self.output.setPlainText("No actions selected.")
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
