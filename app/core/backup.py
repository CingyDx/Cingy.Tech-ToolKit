from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.constants import BACKUPS_DIR


def write_json_backup(name: str, data: dict[str, Any]) -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUPS_DIR / f"{timestamp}_{name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
