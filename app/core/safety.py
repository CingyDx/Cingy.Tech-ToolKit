from __future__ import annotations

from dataclasses import dataclass


class SafetyViolation(RuntimeError):
    """Raised when a planned operation violates the safety model."""


FORBIDDEN_COMMAND_FRAGMENTS = (
    "\n",
    ";",
    "`",
    "|",
    "&&",
    "||",
    "$(",
    "invoke-expression",
    "iex ",
    "disableantispyware",
    "disablerealtimemonitoring",
    "set-mppreference -disable",
    "set-service wuauserv -startuptype disabled",
    "sc.exe config wuauserv start= disabled",
    "slmgr",
    "kms",
    "remove-item c:\\windows",
    "remove-item $env:userprofile\\downloads",
    "rd /s /q c:\\windows",
)


FORBIDDEN_PATH_NAMES = {
    "downloads",
    "documents",
    "desktop",
    "pictures",
    "music",
    "videos",
}


@dataclass(frozen=True, slots=True)
class SafetyCheck:
    allowed: bool
    reason: str = ""


def validate_powershell_script(script: str) -> SafetyCheck:
    normalized = " ".join(script.lower().split())
    for fragment in FORBIDDEN_COMMAND_FRAGMENTS:
        haystack = script.lower() if fragment in {"\n", ";", "`", "|", "&&", "||", "$("} else normalized
        if fragment in haystack:
            return SafetyCheck(False, f"Forbidden PowerShell fragment: {fragment}")
    return SafetyCheck(True)


def assert_safe_powershell_script(script: str) -> None:
    check = validate_powershell_script(script)
    if not check.allowed:
        raise SafetyViolation(check.reason)


def classify_risk(risk_level: str) -> str:
    normalized = risk_level.lower().strip()
    if normalized not in {"safe", "moderate", "risky", "expert"}:
        raise SafetyViolation(f"Unknown risk level: {risk_level}")
    return normalized


def is_dangerous_user_path(path_name: str) -> bool:
    return path_name.lower() in FORBIDDEN_PATH_NAMES
