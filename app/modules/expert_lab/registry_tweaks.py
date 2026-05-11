from __future__ import annotations

from app.constants import RULES_DIR
from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.registry_runner import RegistryRunner
from app.core.state_store import JsonRuleStore


class ExpertRegistryTweaks:
    def __init__(self) -> None:
        self.store = JsonRuleStore(RULES_DIR)
        self.registry = RegistryRunner()

    def rules(self) -> list[dict[str, object]]:
        return self.store.load_required("expert_registry_tweaks.json").get("tweaks", [])

    def actions(self) -> list[Action]:
        return [self._action_from_rule(rule) for rule in self.rules()]

    def _action_from_rule(self, rule: dict[str, object]) -> Action:
        registry = rule["registry"]
        assert isinstance(registry, dict)
        action_id = str(rule["id"])

        def preview(_context):
            current = self.registry.read_value(
                str(registry["hive"]),
                str(registry["path"]),
                str(registry["value_name"]),
            )
            before = {"current_value": current.value if current.exists else None}
            after = {"target_value": registry.get("target_value")}
            return ActionPreview(
                action_id=action_id,
                summary=str(rule["description"]),
                details=[
                    f"{registry['hive']}\\{registry['path']}\\{registry['value_name']}",
                    f"Target: {registry.get('target_value')}",
                    f"Rollback: {registry.get('rollback_value')}",
                ],
                before_values=before,
                after_values=after,
            )

        def execute(_context):
            backup = self.registry.export_key(
                str(registry["hive"]),
                str(registry["path"]),
                action_id.replace(".", "_"),
            )
            current = self.registry.read_value(
                str(registry["hive"]),
                str(registry["path"]),
                str(registry["value_name"]),
            )
            return ActionResult(
                action_id=action_id,
                success=True,
                skipped=True,
                message=(
                    "Registry write is preview-only in the MVP. "
                    f"Backup path: {backup or 'not created in this environment'}"
                ),
                before_values={"current_value": current.value if current.exists else None},
                after_values={"target_value": registry.get("target_value")},
                restart_required=bool(rule.get("requires_restart", False)),
            )

        return Action(
            id=action_id,
            title=str(rule["title"]),
            category="Expert Lab",
            description=str(rule["description"]),
            risk_level=str(rule["risk"]),
            requires_admin=False,
            preview_handler=preview,
            execute_handler=execute,
            affected_registry_keys=[f"{registry['hive']}\\{registry['path']}"],
            rollback_info=f"Rollback value: {registry.get('rollback_value')}",
            selected_by_default=False,
            restart_required=bool(rule.get("requires_restart", False)),
        )
