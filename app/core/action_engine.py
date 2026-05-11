from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.constants import LOGS_DIR
from app.core.action_model import Action, ActionContext, ActionLogEntry, ActionPreview, ActionResult


class ActionExecutionError(RuntimeError):
    """Raised when an action plan cannot execute safely."""


class ActionEngine:
    def __init__(self, context: ActionContext, log_dir: Path | None = None) -> None:
        self.context = context
        self.log_dir = log_dir or LOGS_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_log_path = self.log_dir / f"session_{self.context.session_id}.jsonl"
        self._entries: list[ActionLogEntry] = []

    @property
    def entries(self) -> list[ActionLogEntry]:
        return list(self._entries)

    def default_selected_actions(self, actions: Iterable[Action]) -> list[Action]:
        return [action for action in actions if action.default_selected]

    def preview_plan(self, actions: Iterable[Action]) -> list[ActionPreview]:
        return [action.preview(self.context) for action in actions]

    def execute_plan(
        self,
        actions: Iterable[Action],
        *,
        confirmed: bool,
        allow_risky: bool = False,
    ) -> list[ActionResult]:
        action_list = list(actions)
        if not self.context.dry_run and not confirmed:
            raise ActionExecutionError("Execution requires explicit confirmation.")

        results: list[ActionResult] = []
        for action in action_list:
            self._validate_can_execute(action, allow_risky=allow_risky)
            result = action.execute(self.context)
            results.append(result)
            self._record(action, result)
        return results

    def _validate_can_execute(self, action: Action, *, allow_risky: bool) -> None:
        if action.requires_admin and not self.context.is_admin:
            raise ActionExecutionError(
                f"Administrator access is required before running action '{action.title}'."
            )
        if action.is_risky_or_expert and not allow_risky:
            raise ActionExecutionError(
                f"Risky/expert action '{action.title}' requires an explicit advanced confirmation."
            )

    def _record(self, action: Action, result: ActionResult) -> None:
        entry = ActionLogEntry.from_result(action, result)
        self._entries.append(entry)
        with self.session_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def session_summary(self) -> dict[str, object]:
        return {
            "session_id": self.context.session_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "log_path": str(self.session_log_path),
            "entries": [asdict(entry) for entry in self._entries],
        }
