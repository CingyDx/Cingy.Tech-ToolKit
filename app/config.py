from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.constants import DEFAULT_TECHNICIAN, PROJECT_ROOT


@dataclass(slots=True)
class AppConfig:
    technician_name: str = DEFAULT_TECHNICIAN
    language: str = "cs"
    enable_expert_lab: bool = False
    show_advanced_tools: bool = False
    portable_mode: bool = True
    last_customer_name: str = ""

    @classmethod
    def load(cls, path: Path | None = None) -> "AppConfig":
        config_path = path or PROJECT_ROOT / "app_config.json"
        if not config_path.exists():
            return cls()
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        return cls(**{key: value for key, value in data.items() if key in allowed})

    def save(self, path: Path | None = None) -> None:
        config_path = path or PROJECT_ROOT / "app_config.json"
        config_path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
