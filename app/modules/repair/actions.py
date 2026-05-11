from __future__ import annotations

from app.constants import RULES_DIR
from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.powershell_runner import PowerShellRunner
from app.core.state_store import JsonRuleStore


def get_repair_actions() -> list[Action]:
    runner = PowerShellRunner()
    rules = JsonRuleStore(RULES_DIR).load_required("repair_actions.json").get("actions", [])
    actions: list[Action] = []
    for rule in rules:
        command = rule["command"]
        action_id = rule["id"]

        def preview(_context, *, current_rule=rule):
            warnings = []
            if current_rule.get("restart_required"):
                warnings.append("Restart may be required after this action.")
            return ActionPreview(
                action_id=current_rule["id"],
                summary=current_rule["title"],
                details=[current_rule["command"]],
                warnings=warnings,
            )

        def execute(_context, *, current_rule=rule):
            result = runner.run(current_rule["command"], timeout=3600)
            return ActionResult(
                action_id=current_rule["id"],
                success=result.ok,
                message=f"{current_rule['title']} completed." if result.ok else f"{current_rule['title']} failed.",
                stdout=result.stdout,
                stderr=result.stderr,
                restart_required=bool(current_rule.get("restart_required")),
            )

        actions.append(
            Action(
                id=action_id,
                title=rule["title"],
                category="Repair",
                description=rule["title"],
                risk_level=rule["risk"],
                requires_admin=bool(rule.get("requires_admin", True)),
                preview_handler=preview,
                execute_handler=execute,
                command_preview=runner.preview(command),
                selected_by_default=False,
                restart_required=bool(rule.get("restart_required")),
            )
        )
    return actions
