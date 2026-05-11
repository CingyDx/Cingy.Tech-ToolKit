from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.core.action_engine import ActionEngine
from app.core.action_model import Action, ActionResult


class ActionWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, engine: ActionEngine, actions: list[Action], confirmed: bool, allow_risky: bool = False) -> None:
        super().__init__()
        self.engine = engine
        self.actions = actions
        self.confirmed = confirmed
        self.allow_risky = allow_risky

    @Slot()
    def run(self) -> None:
        try:
            results: list[ActionResult] = self.engine.execute_plan(
                self.actions,
                confirmed=self.confirmed,
                allow_risky=self.allow_risky,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(results)
