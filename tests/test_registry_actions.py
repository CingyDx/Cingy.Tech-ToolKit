from app.core.action_model import ActionContext
from app.modules.expert_lab.registry_tweaks import registry_action_from_rule


class FakeRegistry:
    def __init__(self) -> None:
        self.writes = []

    def read_value(self, _hive, _path, _value_name):
        from app.core.registry_runner import RegistryValue

        return RegistryValue(True, 2, 4)

    def export_key(self, _hive, _path, _backup_name):
        return "backups/example.reg"

    def set_value(self, hive, path, value_name, value_type, value):
        self.writes.append((hive, path, value_name, value_type, value))


def test_safe_registry_action_previews_and_writes_target_value(monkeypatch):
    monkeypatch.setattr(
        "app.modules.expert_lab.registry_tweaks.write_json_backup",
        lambda _name, _data: "backups/example.json",
    )
    rule = {
        "id": "expert.example",
        "title": "Example",
        "risk": "safe",
        "description": "Example tweak",
        "registry": {
            "hive": "HKCU",
            "path": "Software\\Example",
            "value_name": "Enabled",
            "value_type": "REG_DWORD",
            "target_value": 1,
            "rollback_value": 0,
        },
    }
    fake = FakeRegistry()
    action = registry_action_from_rule(rule, fake)

    preview = action.preview(ActionContext(is_admin=False, dry_run=True))
    result = action.execute(ActionContext(is_admin=False, dry_run=False))

    assert preview.before_values["current_value"] == 2
    assert fake.writes == [("HKCU", "Software\\Example", "Enabled", 4, 1)]
    assert result.before_values["backup"] == "backups/example.reg"
    assert result.after_values["target_value"] == 1
