from __future__ import annotations

from app.constants import RULES_DIR
from app.core.state_store import JsonRuleStore


def load_privacy_toggles() -> list[dict[str, object]]:
    return JsonRuleStore(RULES_DIR).load_required("privacy_tweaks.json").get("tweaks", [])
