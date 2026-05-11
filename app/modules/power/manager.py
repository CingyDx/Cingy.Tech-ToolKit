from __future__ import annotations

import re

from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.powershell_runner import PowerShellRunner

_POWERCFG_ALIAS = re.compile(r"^[A-Za-z0-9_-]+$")


class PowerManager:
    def __init__(self) -> None:
        self.runner = PowerShellRunner()

    def current_plan_preview_action(self) -> Action:
        script = "powercfg /GetActiveScheme"

        def execute(_context):
            result = self.runner.run(script, timeout=60)
            return ActionResult(
                action_id="power.current_plan",
                success=result.ok,
                message="Current power plan checked." if result.ok else "Unable to check current power plan.",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        return Action(
            id="power.current_plan",
            title="Check current power plan",
            category="Power & Performance",
            description="Read the active Windows power plan.",
            risk_level="safe",
            requires_admin=False,
            preview_handler=lambda _context: ActionPreview(
                action_id="power.current_plan",
                summary="Reads the active power plan without changing settings.",
            ),
            execute_handler=execute,
            command_preview=self.runner.preview(script),
        )

    def switch_plan_action(self, alias: str, name: str, risk: str = "moderate") -> Action:
        if not _POWERCFG_ALIAS.fullmatch(alias):
            raise ValueError(f"Unsafe powercfg alias: {alias}")
        script = f"powercfg /setactive {alias}"
        return Action(
            id=f"power.switch.{alias.lower()}",
            title=f"Switch to {name}",
            category="Power & Performance",
            description="Switch the active Windows power plan after confirmation.",
            risk_level=risk,
            requires_admin=False,
            preview_handler=lambda _context: ActionPreview(
                action_id=f"power.switch.{alias.lower()}",
                summary=f"Switch active power plan to {name}.",
                warnings=["High performance plans may increase battery usage and heat."],
            ),
            execute_handler=lambda _context: _power_result(f"power.switch.{alias.lower()}", self.runner.run(script, timeout=60)),
            command_preview=self.runner.preview(script),
            selected_by_default=False,
        )


def _power_result(action_id: str, result) -> ActionResult:
    return ActionResult(
        action_id=action_id,
        success=result.ok,
        message="Power plan command completed." if result.ok else "Power plan command failed.",
        stdout=result.stdout,
        stderr=result.stderr,
    )
