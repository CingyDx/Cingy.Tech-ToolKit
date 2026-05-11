from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.constants import RULES_DIR
from app.core.action_model import Action, ActionPreview
from app.core.state_store import JsonRuleStore

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None


@dataclass(slots=True)
class DetectedBloatware:
    name: str
    publisher: str
    app_type: str
    risk: str
    reason: str
    uninstall_method: str
    rule_id: str
    can_remove: bool


class BloatwareManager:
    def __init__(self) -> None:
        self.store = JsonRuleStore(RULES_DIR)

    def rules(self) -> list[dict[str, Any]]:
        return self.store.load_required("bloatware_rules.json").get("rules", [])

    def detect(self) -> list[DetectedBloatware]:
        installed = self._installed_desktop_apps()
        detected: list[DetectedBloatware] = []
        for rule in self.rules():
            patterns = [pattern.lower() for pattern in rule.get("match_patterns", [])]
            for app in installed:
                haystack = f"{app.get('name', '')} {app.get('publisher', '')}".lower()
                if any(pattern in haystack for pattern in patterns):
                    detected.append(
                        DetectedBloatware(
                            name=app.get("name", rule["display_name"]),
                            publisher=app.get("publisher", ""),
                            app_type=rule.get("type", "desktop"),
                            risk=rule.get("risk", "moderate"),
                            reason=rule.get("reason", ""),
                            uninstall_method=rule.get("uninstall_method", "manual_selection"),
                            rule_id=rule.get("id", ""),
                            can_remove=bool(rule.get("can_remove", False)),
                        )
                    )
                    break
        return detected

    def preview_action(self, item: DetectedBloatware) -> Action:
        return Action(
            id=f"debloat.preview.{item.rule_id}",
            title=f"Review {item.name}",
            category="Debloat",
            description=item.reason,
            risk_level=item.risk,
            requires_admin=True,
            preview_handler=lambda _context: ActionPreview(
                action_id=f"debloat.preview.{item.rule_id}",
                summary=f"{item.name} is eligible for manual review.",
                details=[f"Publisher: {item.publisher}", f"Method: {item.uninstall_method}"],
                warnings=[] if item.can_remove else ["Rule is marked can_remove=false; no uninstall action will be created."],
            ),
            selected_by_default=False,
            affected_packages=[item.name],
        )

    def _installed_desktop_apps(self) -> list[dict[str, str]]:
        if winreg is None:
            return []
        roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        apps: list[dict[str, str]] = []
        for hive, path in roots:
            try:
                with winreg.OpenKey(hive, path) as key:
                    for index in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, index)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                try:
                                    publisher, _ = winreg.QueryValueEx(subkey, "Publisher")
                                except OSError:
                                    publisher = ""
                                apps.append({"name": str(name), "publisher": str(publisher)})
                        except OSError:
                            continue
            except OSError:
                continue
        return apps
