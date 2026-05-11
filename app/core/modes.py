from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.constants import RULES_DIR
from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.restore_point import create_restore_point_action
from app.core.state_store import JsonRuleStore
from app.modules.cleanup import get_cleanup_actions
from app.modules.power import PowerManager
from app.modules.repair import get_repair_actions
from app.modules.updates import InstallPackStore


FRIENDLY_ACTION_TITLES = {
    "scan.system": "Rychlá kontrola PC",
    "restore_point.create": "Bod obnovení systému",
    "restore_point.create_if_admin": "Bod obnovení systému",
    "cleanup.user_temp": "Vyčištění dočasných souborů",
    "cleanup.windows_temp": "Vyčištění systémových dočasných souborů",
    "cleanup.recycle_bin": "Vysypání koše po potvrzení",
    "cleanup.thumbnail_cache": "Vyčištění náhledů obrázků",
    "cleanup.directx_shader_cache": "Vyčištění DirectX cache",
    "cleanup.delivery_optimization": "Vyčištění cache aktualizací",
    "cleanup.downloads_report": "Přehled velkých souborů ve Stažených",
    "startup.review": "Kontrola aplikací po startu",
    "debloat.detect": "Kontrola zbytečných aplikací",
    "debloat.manual_selection": "Ruční výběr aplikací k odebrání",
    "winget.sources.update_preview": "Kontrola katalogu aplikací",
    "winget.outdated.check": "Kontrola zastaralých aplikací",
    "install_packs.offer": "Nabídka běžných aplikací",
    "privacy.safe_toggles": "Základní nastavení soukromí",
    "power.current_plan": "Kontrola napájení",
    "power.recommend_profile": "Doporučení režimu napájení",
    "gaming.game_mode.check": "Kontrola Herního režimu Windows",
    "gaming.xbox_game_bar.check": "Kontrola Xbox Game Baru",
    "gpu.driver_info.check": "Informace o grafické kartě",
    "storage.game_drives.check": "Kontrola místa na discích pro hry",
    "startup.gaming_impact.review": "Aplikace po startu ovlivňující hraní",
    "folders.school_work_backup.offer": "Návrh složek pro školu a práci",
    "repair.sfc_scan": "Oprava systémových souborů",
    "repair.dism_checkhealth": "Kontrola obrazu Windows",
    "repair.dism_scanhealth": "Hloubková kontrola obrazu Windows",
    "repair.dism_restorehealth": "Oprava obrazu Windows",
    "repair.chkdsk_scan": "Kontrola disku",
    "repair.flush_dns": "Vyčištění DNS cache",
    "repair.winsock_reset": "Oprava síťových služeb",
    "repair.ip_stack_reset": "Obnovení nastavení internetu",
    "repair.windows_update.basic": "Základní oprava Windows Update",
    "event_log.summary": "Přehled systémových varování",
    "report.generate": "Servisní report",
    "report.generate_detailed": "Detailní servisní report",
    "expert.warning_gate": "Potvrzení Technik / Expert",
    "expert.registry.preview": "Náhled pokročilých nastavení",
    "expert.registry.apply_selected_only": "Pouze vybrané expert změny",
}


FRIENDLY_ACTION_DESCRIPTIONS = {
    "scan.system": "Zjistí základní stav počítače bez provádění změn.",
    "startup.review": "Ukáže aplikace, které se spouští po startu Windows.",
    "debloat.detect": "Najde běžné předinstalované nebo zkušební aplikace.",
    "debloat.manual_selection": "Nic neodebere automaticky. Technik vybere položky ručně.",
    "winget.sources.update_preview": "Pouze zkontroluje dostupnost katalogu aplikací.",
    "winget.outdated.check": "Ukáže aplikace, které mohou mít dostupnou aktualizaci.",
    "install_packs.offer": "Nabídne běžné balíčky aplikací. Instalace se nespouští automaticky.",
    "privacy.safe_toggles": "Zobrazí bezpečná nastavení Windows s vysvětlením.",
    "power.recommend_profile": "Zkontroluje, zda dává smysl změnit režim napájení.",
    "gaming.game_mode.check": "Zkontroluje nastavení, která mohou ovlivnit hraní.",
    "gaming.xbox_game_bar.check": "Ukáže stav herních doplňků Windows.",
    "gpu.driver_info.check": "Zobrazí dostupné informace o grafické kartě.",
    "storage.game_drives.check": "Upozorní na málo místa na discích s hrami.",
    "startup.gaming_impact.review": "Najde aplikace po startu, které mohou zbytečně běžet na pozadí.",
    "folders.school_work_backup.offer": "Navrhne základní složky pro školu, práci a zálohu dokumentů.",
    "repair.windows_update.basic": "Připraví bezpečný postup pro řešení běžných problémů s aktualizacemi.",
    "event_log.summary": "Shrne důležité systémové události pro technika.",
    "report.generate": "Vytvoří zákaznický servisní report.",
    "report.generate_detailed": "Vytvoří detailní report pro technika.",
}


@dataclass(frozen=True, slots=True)
class ModeDefinition:
    id: str
    title_cs: str
    title_en: str
    short_description_cs: str
    long_description_cs: str
    risk: str
    recommended_for: list[str]
    action_ids: list[str]
    visible_by_default: bool
    technician_only: bool
    icon: str
    safety_notes: list[str]
    never_does: list[str]
    checklist: list[str]


@dataclass(slots=True)
class ModePlan:
    mode_id: str
    actions: list[Action]
    default_selected_actions: list[Action]
    requires_admin_count: int
    risky_count: int
    advanced_count: int
    estimated_cleanup_bytes: int = 0

    @property
    def total_actions(self) -> int:
        return len(self.actions)


class ModeCatalog:
    def __init__(self, modes: list[ModeDefinition]) -> None:
        self._modes = modes
        self._by_id = {mode.id: mode for mode in modes}

    @classmethod
    def load_default(cls) -> "ModeCatalog":
        data = JsonRuleStore(RULES_DIR).load_required("modes.json")
        modes = [ModeDefinition(**item) for item in data.get("modes", [])]
        return cls(modes)

    def all_modes(self) -> list[ModeDefinition]:
        return list(self._modes)

    def visible_modes(self, *, include_technician: bool = False) -> list[ModeDefinition]:
        return [
            mode
            for mode in self._modes
            if mode.visible_by_default or (include_technician and mode.technician_only)
        ]

    def get(self, mode_id: str) -> ModeDefinition:
        return self._by_id[mode_id]


def friendly_action_title(action_id: str) -> str:
    return FRIENDLY_ACTION_TITLES.get(action_id, action_id.replace("_", " ").replace(".", " ").title())


def friendly_action_description(action_id: str) -> str:
    return FRIENDLY_ACTION_DESCRIPTIONS.get(action_id, "Akce se před spuštěním zobrazí v náhledu plánu.")


def build_mode_plan(mode: ModeDefinition, *, is_admin: bool) -> ModePlan:
    actions_by_id = _available_actions(is_admin=is_admin)
    actions: list[Action] = []
    seen: set[str] = set()
    for action_id in mode.action_ids:
        action = actions_by_id.get(action_id)
        if action is None:
            action = _placeholder_action(action_id, mode.risk)
        if action.id in seen:
            continue
        seen.add(action.id)
        actions.append(action)

    default_selected = [action for action in actions if action.default_selected and not action.is_risky_or_expert]
    return ModePlan(
        mode_id=mode.id,
        actions=actions,
        default_selected_actions=default_selected,
        requires_admin_count=sum(1 for action in actions if action.requires_admin),
        risky_count=sum(1 for action in actions if action.risk_level == "risky"),
        advanced_count=sum(1 for action in actions if action.risk_level == "expert"),
    )


def _available_actions(*, is_admin: bool) -> dict[str, Action]:
    actions: list[Action] = []
    actions.append(_scan_action())
    actions.append(create_restore_point_action())
    actions.extend(get_cleanup_actions())
    actions.extend(get_repair_actions())
    actions.append(PowerManager().current_plan_preview_action())
    actions.extend(InstallPackStore().preview_actions())

    by_id = {action.id: action for action in actions}
    by_id["restore_point.create_if_admin"] = by_id["restore_point.create"]
    for alias in (
        "startup.review",
        "debloat.detect",
        "debloat.manual_selection",
        "winget.sources.update_preview",
        "winget.outdated.check",
        "install_packs.offer",
        "privacy.safe_toggles",
        "power.recommend_profile",
        "gaming.game_mode.check",
        "gaming.xbox_game_bar.check",
        "gpu.driver_info.check",
        "storage.game_drives.check",
        "startup.gaming_impact.review",
        "folders.school_work_backup.offer",
        "repair.windows_update.basic",
        "event_log.summary",
        "report.generate",
        "report.generate_detailed",
        "expert.warning_gate",
        "expert.registry.preview",
        "expert.registry.apply_selected_only",
    ):
        by_id[alias] = _placeholder_action(alias, _risk_for_alias(alias))
    return by_id


def _scan_action() -> Action:
    return Action(
        id="scan.system",
        title=friendly_action_title("scan.system"),
        category="Bezpečné",
        description=friendly_action_description("scan.system"),
        risk_level="safe",
        requires_admin=False,
        preview_handler=lambda _context: ActionPreview(
            action_id="scan.system",
            summary="Kontrola PC připraví přehled stavu bez změn v systému.",
        ),
        execute_handler=lambda _context: ActionResult(
            action_id="scan.system",
            success=True,
            skipped=True,
            message="Kontrola se spouští z obrazovky Kontrola PC; tato položka je informační.",
        ),
    )


def _placeholder_action(action_id: str, risk: str) -> Action:
    title = friendly_action_title(action_id)
    return Action(
        id=action_id,
        title=title,
        category=_category_for_action(action_id, risk),
        description=friendly_action_description(action_id),
        risk_level=risk,
        requires_admin=action_id.startswith("repair.") and action_id != "repair.flush_dns",
        preview_handler=lambda _context, *, current_id=action_id, current_title=title: ActionPreview(
            action_id=current_id,
            summary=current_title,
            details=[friendly_action_description(current_id)],
            warnings=["Tato položka je v MVP jen bezpečný náhled nebo doporučení."],
        ),
        execute_handler=lambda _context, *, current_id=action_id, current_title=title: ActionResult(
            action_id=current_id,
            success=True,
            skipped=True,
            message=f"{current_title}: v MVP pouze náhled / doporučení.",
        ),
        selected_by_default=(risk == "safe"),
    )


def _risk_for_alias(action_id: str) -> str:
    if action_id.startswith("expert."):
        return "expert"
    if action_id in {"repair.windows_update.basic", "event_log.summary"}:
        return "moderate"
    if action_id in {"debloat.manual_selection", "power.recommend_profile"}:
        return "moderate"
    return "safe"


def _category_for_action(action_id: str, risk: str) -> str:
    if risk == "expert":
        return "Pokročilé"
    if action_id.startswith("repair."):
        return "Vyžaduje správce"
    if risk == "moderate":
        return "Volitelné"
    return "Bezpečné"
