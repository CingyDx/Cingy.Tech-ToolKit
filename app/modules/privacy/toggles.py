from __future__ import annotations

from app.constants import RULES_DIR
from app.core.registry_runner import RegistryRunner
from app.core.state_store import JsonRuleStore
from app.modules.expert_lab.registry_tweaks import registry_action_from_rule


def load_privacy_toggles() -> list[dict[str, object]]:
    return JsonRuleStore(RULES_DIR).load_required("privacy_tweaks.json").get("tweaks", [])


def privacy_toggle_actions():
    registry = RegistryRunner()
    actions = []
    for rule in load_privacy_toggles():
        if "registry" not in rule:
            continue
        actions.append(registry_action_from_rule(rule, registry))
    return actions
