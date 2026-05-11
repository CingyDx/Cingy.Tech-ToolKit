from __future__ import annotations

from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.powershell_runner import PowerShellRunner


RESTORE_POINT_SCRIPT = (
    'Checkpoint-Computer -Description "Cingy.Tech ToolKit pre-service checkpoint" '
    '-RestorePointType "MODIFY_SETTINGS"'
)


def create_restore_point_action() -> Action:
    runner = PowerShellRunner()

    def preview(_context):
        return ActionPreview(
            action_id="restore_point.create",
            summary="Create a Windows restore point before system-changing actions.",
            details=[
                "Requires Administrator access.",
                "Windows may throttle restore point creation if one was created recently.",
            ],
        )

    def execute(_context):
        result = runner.run(RESTORE_POINT_SCRIPT, timeout=300)
        return ActionResult(
            action_id="restore_point.create",
            success=result.ok,
            message="Restore point command completed." if result.ok else "Restore point command failed.",
            stdout=result.stdout,
            stderr=result.stderr,
        )

    return Action(
        id="restore_point.create",
        title="Create restore point",
        category="Safety",
        description="Create a Windows restore point before technician changes.",
        risk_level="safe",
        requires_admin=True,
        preview_handler=preview,
        execute_handler=execute,
        rollback_info="Use Windows System Restore to roll back system configuration changes.",
        command_preview=runner.preview(RESTORE_POINT_SCRIPT),
    )
