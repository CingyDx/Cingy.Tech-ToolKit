from __future__ import annotations

from pathlib import Path

APP_NAME = "Cingy.Tech ToolKit"
APP_SUBTITLE = "Windows Optimizer & Service Suite"
DEFAULT_TECHNICIAN = "Kryštof Cingálek / Cingy.Tech"

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"
BACKUPS_DIR = PROJECT_ROOT / "backups"
RULES_DIR = APP_DIR / "rules"
ASSETS_DIR = APP_DIR / "assets"
TEMPLATE_DIR = APP_DIR / "reports" / "templates"

LOCAL_DATA_DIRS = (LOGS_DIR, REPORTS_DIR, BACKUPS_DIR)

RISK_SAFE = "safe"
RISK_MODERATE = "moderate"
RISK_RISKY = "risky"
RISK_EXPERT = "expert"
RISK_LEVELS = (RISK_SAFE, RISK_MODERATE, RISK_RISKY, RISK_EXPERT)

SERVICE_CHECKLIST_ITEMS = [
    "Záloha důležitých dat ověřena",
    "Restore point vytvořen",
    "Disk health zkontrolován",
    "Startup optimalizován",
    "Bloatware odstraněn",
    "SFC/DISM hotovo",
    "Restart proveden",
    "Zákazníkovi předán report",
]


def ensure_local_directories() -> None:
    for directory in LOCAL_DATA_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
