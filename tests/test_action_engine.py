import pytest

from app.core.action_engine import ActionEngine, ActionExecutionError
from app.core.action_model import Action, ActionContext, ActionPreview, ActionResult


def test_action_engine_previews_without_executing():
    calls = {"execute": 0}

    def preview(_context):
        return ActionPreview(action_id="cleanup.user_temp", summary="Would clean temp files")

    def execute(_context):
        calls["execute"] += 1
        return ActionResult(action_id="cleanup.user_temp", success=True, message="cleaned")

    action = Action(
        id="cleanup.user_temp",
        title="Clean user temp",
        category="Cleanup",
        description="Remove files from the current user's temp directory.",
        risk_level="safe",
        requires_admin=False,
        preview_handler=preview,
        execute_handler=execute,
    )

    engine = ActionEngine(context=ActionContext(is_admin=False, dry_run=True))

    previews = engine.preview_plan([action])

    assert previews[0].summary == "Would clean temp files"
    assert calls["execute"] == 0


def test_action_engine_requires_explicit_confirmation_before_execute():
    action = Action(
        id="cleanup.user_temp",
        title="Clean user temp",
        category="Cleanup",
        description="Remove files from the current user's temp directory.",
        risk_level="safe",
        requires_admin=False,
        preview_handler=lambda _context: ActionPreview(action_id="cleanup.user_temp", summary="preview"),
        execute_handler=lambda _context: ActionResult(action_id="cleanup.user_temp", success=True, message="done"),
    )

    engine = ActionEngine(context=ActionContext(is_admin=False, dry_run=False))

    with pytest.raises(ActionExecutionError, match="confirmation"):
        engine.execute_plan([action], confirmed=False)


def test_action_engine_blocks_admin_action_when_not_elevated():
    action = Action(
        id="restore_point.create",
        title="Create restore point",
        category="Safety",
        description="Create a Windows restore point.",
        risk_level="safe",
        requires_admin=True,
        preview_handler=lambda _context: ActionPreview(action_id="restore_point.create", summary="preview"),
        execute_handler=lambda _context: ActionResult(action_id="restore_point.create", success=True, message="done"),
    )

    engine = ActionEngine(context=ActionContext(is_admin=False, dry_run=False))

    with pytest.raises(ActionExecutionError, match="Administrator"):
        engine.execute_plan([action], confirmed=True)


def test_risky_and_expert_actions_are_not_selected_by_default():
    safe = Action(
        id="cleanup.user_temp",
        title="Clean user temp",
        category="Cleanup",
        description="Remove files from the current user's temp directory.",
        risk_level="safe",
        requires_admin=False,
    )
    expert = Action(
        id="expert.registry.sample",
        title="Sample registry tweak",
        category="Expert Lab",
        description="A sample expert registry tweak.",
        risk_level="expert",
        requires_admin=True,
    )

    engine = ActionEngine(context=ActionContext(is_admin=True))

    selected = engine.default_selected_actions([safe, expert])

    assert [action.id for action in selected] == ["cleanup.user_temp"]
