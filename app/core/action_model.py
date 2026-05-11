from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from app.constants import DEFAULT_TECHNICIAN
from app.core.safety import classify_risk

PreviewHandler = Callable[["ActionContext"], "ActionPreview"]
ExecuteHandler = Callable[["ActionContext"], "ActionResult"]


@dataclass(slots=True)
class ActionContext:
    is_admin: bool
    dry_run: bool = True
    technician_name: str = DEFAULT_TECHNICIAN
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActionPreview:
    action_id: str
    summary: str
    details: list[str] = field(default_factory=list)
    estimated_bytes: int = 0
    warnings: list[str] = field(default_factory=list)
    before_values: dict[str, Any] = field(default_factory=dict)
    after_values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActionResult:
    action_id: str
    success: bool
    message: str
    stdout: str = ""
    stderr: str = ""
    skipped: bool = False
    restart_required: bool = False
    before_values: dict[str, Any] = field(default_factory=dict)
    after_values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Action:
    id: str
    title: str
    category: str
    description: str
    risk_level: str
    requires_admin: bool
    preview_handler: PreviewHandler | None = None
    execute_handler: ExecuteHandler | None = None
    rollback_info: str | None = None
    affected_paths: list[str] = field(default_factory=list)
    affected_registry_keys: list[str] = field(default_factory=list)
    affected_packages: list[str] = field(default_factory=list)
    command_preview: str | None = None
    selected_by_default: bool | None = None
    restart_required: bool = False

    def __post_init__(self) -> None:
        self.risk_level = classify_risk(self.risk_level)

    @property
    def is_risky_or_expert(self) -> bool:
        return self.risk_level in {"risky", "expert"}

    @property
    def default_selected(self) -> bool:
        if self.is_risky_or_expert:
            return False
        if self.selected_by_default is not None:
            return bool(self.selected_by_default)
        return self.risk_level == "safe"

    def preview(self, context: ActionContext) -> ActionPreview:
        if self.preview_handler:
            return self.preview_handler(context)
        return ActionPreview(action_id=self.id, summary=self.description)

    def execute(self, context: ActionContext) -> ActionResult:
        if context.dry_run:
            return ActionResult(
                action_id=self.id,
                success=True,
                skipped=True,
                message=f"Dry run only: {self.title}",
                restart_required=self.restart_required,
            )
        if self.execute_handler:
            return self.execute_handler(context)
        return ActionResult(
            action_id=self.id,
            success=False,
            skipped=True,
            message="No executor is implemented for this MVP action.",
            restart_required=self.restart_required,
        )


@dataclass(slots=True)
class ServiceChecklistItem:
    label: str
    checked: bool = False


@dataclass(slots=True)
class CustomerJobProfile:
    customer_name: str = ""
    device: str = ""
    job: str = ""
    problem: str = ""
    price: str = ""
    notes: str = ""


@dataclass(slots=True)
class SnapshotPair:
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActionLogEntry:
    timestamp: str
    action_id: str
    action_title: str
    command: str | None
    result: str
    stdout_summary: str = ""
    stderr_summary: str = ""
    before_values: dict[str, Any] = field(default_factory=dict)
    after_values: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_result(cls, action: Action, result: ActionResult) -> "ActionLogEntry":
        return cls(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            action_id=action.id,
            action_title=action.title,
            command=action.command_preview,
            result=result.message,
            stdout_summary=result.stdout[:800],
            stderr_summary=result.stderr[:800],
            before_values=result.before_values,
            after_values=result.after_values,
        )
