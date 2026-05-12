from __future__ import annotations

from app.constants import RULES_DIR
from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.backup import write_json_backup
from app.core.registry_runner import RegistryRunner
from app.core.state_store import JsonRuleStore


REGISTRY_VALUE_TYPES = {
    "REG_SZ": 1,
    "REG_EXPAND_SZ": 2,
    "REG_DWORD": 4,
    "REG_QWORD": 11,
}


class ExpertRegistryTweaks:
    def __init__(self) -> None:
        self.store = JsonRuleStore(RULES_DIR)
        self.registry = RegistryRunner()

    def rules(self) -> list[dict[str, object]]:
        return self.store.load_required("expert_registry_tweaks.json").get("tweaks", [])

    def actions(self) -> list[Action]:
        return [registry_action_from_rule(rule, self.registry) for rule in self.rules()]

    def _action_from_rule(self, rule: dict[str, object]) -> Action:
        return registry_action_from_rule(rule, self.registry)


def registry_action_from_rule(rule: dict[str, object], registry: RegistryRunner) -> Action:
    registry_rule = rule["registry"]
    assert isinstance(registry_rule, dict)
    action_id = str(rule["id"])
    hive = str(registry_rule["hive"])
    path = str(registry_rule["path"])
    value_name = str(registry_rule["value_name"])
    value_type = _value_type_from_rule(str(registry_rule["value_type"]))
    target_value = registry_rule.get("target_value")
    rollback_value = registry_rule.get("rollback_value")

    def preview(_context):
        current = registry.read_value(hive, path, value_name)
        before = {"current_value": current.value if current.exists else None}
        after = {"target_value": target_value}
        return ActionPreview(
            action_id=action_id,
            summary=str(rule["description"]),
            details=[
                f"{hive}\\{path}\\{value_name}",
                f"Cílová hodnota: {target_value}",
                f"Návratová hodnota: {rollback_value}",
            ],
            before_values=before,
            after_values=after,
        )

    def execute(_context):
        if str(rule["risk"]) != "safe" or hive != "HKCU":
            return ActionResult(
                action_id=action_id,
                success=False,
                skipped=True,
                message="Registry zápis je povolený jen pro bezpečné HKCU položky.",
            )
        current = registry.read_value(hive, path, value_name)
        backup = registry.export_key(hive, path, action_id.replace(".", "_"))
        json_backup = write_json_backup(
            action_id.replace(".", "_"),
            {
                "action_id": action_id,
                "hive": hive,
                "path": path,
                "value_name": value_name,
                "previous_exists": current.exists,
                "previous_value": current.value if current.exists else None,
                "previous_type": current.value_type,
                "target_value": target_value,
                "rollback_value": rollback_value,
            },
        )
        registry.set_value(hive, path, value_name, value_type, target_value)
        return ActionResult(
            action_id=action_id,
            success=True,
            message=f"Nastavení bylo použito: {rule['title']}.",
            before_values={
                "current_value": current.value if current.exists else None,
                "backup": str(backup or json_backup),
            },
            after_values={"target_value": target_value},
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
        affected_registry_keys=[f"{hive}\\{path}"],
        rollback_info=f"Rollback value: {rollback_value}",
        selected_by_default=False,
        restart_required=bool(rule.get("requires_restart", False)),
    )


def registry_undo_action_from_rule(rule: dict[str, object], registry: RegistryRunner) -> Action:
    registry_rule = rule["registry"]
    assert isinstance(registry_rule, dict)
    undo_rule = dict(rule)
    undo_registry = dict(registry_rule)
    undo_registry["target_value"] = registry_rule.get("rollback_value")
    undo_registry["rollback_value"] = registry_rule.get("target_value")
    undo_rule["id"] = f"{rule['id']}.undo"
    undo_rule["title"] = f"Vrátit zpět: {rule['title']}"
    undo_rule["description"] = f"Vrátí hodnotu pro {rule['title']} na rollback hodnotu."
    undo_rule["registry"] = undo_registry
    return registry_action_from_rule(undo_rule, registry)


def _value_type_from_rule(value_type: str) -> int:
    normalized = value_type.upper().strip()
    if normalized not in REGISTRY_VALUE_TYPES:
        raise ValueError(f"Nepodporovaný typ registru: {value_type}")
    return REGISTRY_VALUE_TYPES[normalized]
