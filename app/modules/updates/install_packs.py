from __future__ import annotations

from app.constants import RULES_DIR
from app.core.action_model import Action, ActionPreview
from app.core.state_store import JsonRuleStore


class InstallPackStore:
    def __init__(self) -> None:
        self.store = JsonRuleStore(RULES_DIR)

    def packs(self) -> list[dict[str, object]]:
        return self.store.load_required("install_packs.json").get("packs", [])

    def preview_actions(self) -> list[Action]:
        actions: list[Action] = []
        for pack in self.packs():
            pack_id = str(pack["id"])
            packages = pack.get("packages", [])
            assert isinstance(packages, list)
            package_lines = [
                f"{item.get('name')} - {item.get('winget_id') or item.get('todo', 'package ID not enabled')}"
                for item in packages
                if isinstance(item, dict)
            ]
            actions.append(
                Action(
                    id=f"install_pack.preview.{pack_id}",
                    title=f"Preview {pack['name']}",
                    category="Install Packs",
                    description="Preview winget package IDs. Nothing installs automatically.",
                    risk_level="safe",
                    requires_admin=False,
                    preview_handler=lambda _context, *, current_pack=pack, lines=package_lines: ActionPreview(
                        action_id=f"install_pack.preview.{current_pack['id']}",
                        summary=f"{current_pack['name']} contains {len(lines)} packages.",
                        details=lines,
                    ),
                    selected_by_default=False,
                )
            )
        return actions
