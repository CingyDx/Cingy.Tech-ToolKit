from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.admin import is_windows
from app.constants import BACKUPS_DIR

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None


HIVES = {
    "HKCU": getattr(winreg, "HKEY_CURRENT_USER", None),
    "HKLM": getattr(winreg, "HKEY_LOCAL_MACHINE", None),
}


@dataclass(slots=True)
class RegistryValue:
    exists: bool
    value: Any = None
    value_type: int | None = None


class RegistryRunner:
    def read_value(self, hive_name: str, path: str, value_name: str) -> RegistryValue:
        if not is_windows() or winreg is None:
            return RegistryValue(False)
        hive = HIVES.get(hive_name)
        if hive is None:
            return RegistryValue(False)
        try:
            with winreg.OpenKey(hive, path) as key:
                value, value_type = winreg.QueryValueEx(key, value_name)
            return RegistryValue(True, value, value_type)
        except OSError:
            return RegistryValue(False)

    def export_key(self, hive_name: str, path: str, backup_name: str) -> Path | None:
        if not is_windows():
            return None
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        output = BACKUPS_DIR / f"{backup_name}.reg"
        key = f"{hive_name}\\{path}"
        completed = subprocess.run(
            ["reg.exe", "export", key, str(output), "/y"],
            capture_output=True,
            text=True,
            shell=False,
        )
        if completed.returncode != 0:
            return None
        return output

    def set_value(self, hive_name: str, path: str, value_name: str, value_type: int, value: Any) -> None:
        if not is_windows() or winreg is None:
            return
        hive = HIVES.get(hive_name)
        if hive is None:
            return
        with winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, value_name, 0, value_type, value)
