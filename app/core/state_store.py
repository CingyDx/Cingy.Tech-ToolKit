from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class JsonRuleStore:
    def __init__(self, rules_dir: Path) -> None:
        self.rules_dir = Path(rules_dir)

    def load_required(self, filename: str) -> dict[str, Any]:
        path = self.rules_dir / filename
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"{filename} must contain a JSON object.")
        return data

    def validate_rule_file(self, filename: str, required_fields: Iterable[str]) -> list[str]:
        path = self.rules_dir / filename
        if not path.exists():
            return [f"{filename}: file is missing"]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return [f"{filename}: invalid JSON at line {exc.lineno}: {exc.msg}"]

        items = _extract_rule_items(data)
        errors: list[str] = []
        required = set(required_fields)
        for index, item in enumerate(items):
            missing = sorted(required - set(item))
            if missing:
                errors.append(f"{filename}[{index}] missing required field(s): {', '.join(missing)}")
        return errors

    def validate_startup_rules(self) -> list[str]:
        checks = {
            "presets.json": {"id", "name", "purpose", "actions"},
            "bloatware_rules.json": {"id", "display_name", "match_patterns", "type", "risk", "recommended_for_presets", "reason", "can_remove"},
            "startup_rules.json": {"id", "name", "match_patterns", "recommendation", "risk"},
            "cleanup_rules.json": {"id", "title", "risk", "target"},
            "power_profiles.json": {"id", "name", "risk"},
            "repair_actions.json": {"id", "title", "risk", "command"},
            "privacy_tweaks.json": {"id", "title", "risk"},
            "install_packs.json": {"id", "name", "packages"},
            "expert_registry_tweaks.json": {"id", "title", "risk", "registry"},
            "modes.json": {"id", "title_cs", "short_description_cs", "risk", "action_ids", "visible_by_default", "technician_only"},
        }
        errors: list[str] = []
        for filename, fields in checks.items():
            errors.extend(self.validate_rule_file(filename, fields))
        return errors


def _extract_rule_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [data]
    return []
