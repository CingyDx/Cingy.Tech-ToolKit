from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.powershell_runner import PowerShellRunner, PowerShellResult

_POWERCFG_GUID = re.compile(r"^[0-9a-fA-F-]{36}$")
_POWER_SCHEME_LINE = re.compile(
    r"Power Scheme GUID:\s*([0-9a-fA-F-]{36})\s+\((.*?)\)\s*(\*)?",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class PowerPlan:
    guid: str
    name: str
    is_active: bool = False


def parse_power_plans(output: str) -> list[PowerPlan]:
    plans: list[PowerPlan] = []
    for match in _POWER_SCHEME_LINE.finditer(output):
        plans.append(
            PowerPlan(
                guid=match.group(1).lower(),
                name=match.group(2).strip(),
                is_active=bool(match.group(3)),
            )
        )
    if plans and not any(plan.is_active for plan in plans) and len(plans) == 1:
        only_plan = plans[0]
        plans[0] = PowerPlan(only_plan.guid, only_plan.name, True)
    return plans


class PowerManager:
    def __init__(self) -> None:
        self.runner = PowerShellRunner()

    def list_power_plans(self) -> list[PowerPlan]:
        result = self.runner.run("powercfg /L", timeout=60)
        if not result.ok:
            return []
        return parse_power_plans(result.stdout)

    def current_plan_preview_action(self) -> Action:
        script = "powercfg /GetActiveScheme"

        def execute(_context):
            result = self.runner.run(script, timeout=60)
            if result.ok:
                plan = _first_power_plan(result.stdout)
                if plan:
                    message = f"Aktuální režim napájení: {plan.name}."
                else:
                    message = "Aktuální režim napájení zkontrolován. Detail je v technickém výpisu."
            else:
                message = "Nepodařilo se zkontrolovat aktuální režim napájení."
            return ActionResult(
                action_id="power.current_plan",
                success=result.ok,
                message=message,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        return Action(
            id="power.current_plan",
            title="Kontrola napájení",
            category="Power & Performance",
            description="Přečte aktuální režim napájení Windows bez změn.",
            risk_level="safe",
            requires_admin=False,
            preview_handler=lambda _context: ActionPreview(
                action_id="power.current_plan",
                summary="Zobrazí aktuální režim napájení. Nic nemění.",
            ),
            execute_handler=execute,
            command_preview=self.runner.preview(script),
        )

    def switch_plan_action(self, guid: str, name: str, risk: str = "moderate") -> Action:
        normalized_guid = guid.strip().lower()
        if not _POWERCFG_GUID.fullmatch(normalized_guid):
            raise ValueError(f"Unsafe powercfg GUID: {guid}")
        script = f"powercfg /setactive {normalized_guid}"
        action_id = f"power.switch.{normalized_guid}"

        def execute(_context):
            result = self.runner.run(script, timeout=60)
            return _power_result(
                action_id,
                result,
                success_message=f"Režim napájení byl přepnut na: {name}.",
                failure_message=f"Režim napájení se nepodařilo přepnout na: {name}.",
            )

        return Action(
            id=action_id,
            title=f"Přepnout na {name}",
            category="Power & Performance",
            description="Přepne aktivní režim napájení Windows po potvrzení.",
            risk_level=risk,
            requires_admin=False,
            preview_handler=lambda _context: ActionPreview(
                action_id=action_id,
                summary=f"Přepne aktivní režim napájení na {name}.",
                warnings=["Výkonnější režimy mohou zvýšit spotřebu baterie a zahřívání."],
            ),
            execute_handler=execute,
            command_preview=self.runner.preview(script),
            selected_by_default=False,
        )


def _first_power_plan(output: str) -> PowerPlan | None:
    plans = parse_power_plans(output)
    if not plans:
        return None
    return next((plan for plan in plans if plan.is_active), plans[0])


def _power_result(
    action_id: str,
    result: PowerShellResult,
    *,
    success_message: str,
    failure_message: str,
) -> ActionResult:
    return ActionResult(
        action_id=action_id,
        success=result.ok,
        message=success_message if result.ok else failure_message,
        stdout=result.stdout,
        stderr=result.stderr,
    )
