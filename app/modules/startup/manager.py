from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote

from app.constants import BACKUPS_DIR

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None

_HKCU_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_BACKUP_FILE = BACKUPS_DIR / "startup_disabled.json"
_PROTECTED_STARTUP_WORDS = (
    "defender",
    "securityhealth",
    "windows security",
    "microsoft security",
    "antivirus",
)


@dataclass(slots=True)
class StartupEntry:
    id: str
    name: str
    source: str
    command: str
    publisher: str = ""
    recommendation: str = "Zkontrolovat ručně"
    risk: str = "moderate"
    enabled: bool = True
    can_disable: bool = False
    can_enable: bool = False


class StartupManager:
    def list_entries(self) -> list[StartupEntry]:
        entries = self._registry_entries()
        entries.extend(self._disabled_registry_entries(entries))
        entries.extend(self._startup_folder_entries())
        return entries

    def disable_entry(self, entry_id: str) -> str:
        if winreg is None:
            raise RuntimeError("Startup úpravy jsou dostupné pouze ve Windows.")
        name = _decode_hkcu_run_id(entry_id)
        if not name:
            raise ValueError("Tuto položku zatím umíme bezpečně vypnout jen v HKCU Run.")
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _HKCU_RUN_PATH, 0, winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as key:
            command, kind = winreg.QueryValueEx(key, name)
            _assert_startup_entry_is_safe_to_disable(name, str(command))
            backup = _load_backup()
            backup[entry_id] = {
                "name": name,
                "command": str(command),
                "kind": int(kind),
                "source": "HKCU Run",
            }
            _save_backup(backup)
            winreg.DeleteValue(key, name)
        return f"Položka po startu byla vypnutá: {name}. Záloha je uložená v backups/startup_disabled.json."

    def enable_entry(self, entry_id: str) -> str:
        if winreg is None:
            raise RuntimeError("Startup úpravy jsou dostupné pouze ve Windows.")
        backup = _load_backup()
        payload = backup.get(entry_id)
        if not payload:
            raise ValueError("Pro tuto položku není uložená záloha.")
        decoded_name = _decode_hkcu_run_id(entry_id)
        name = str(payload["name"])
        command = str(payload["command"])
        if decoded_name != name or payload.get("source") != "HKCU Run" or not command:
            raise ValueError("Záloha startup položky nevypadá důvěryhodně, obnova byla zastavena.")
        kind = int(payload.get("kind", winreg.REG_SZ))
        if kind not in {winreg.REG_SZ, winreg.REG_EXPAND_SZ}:
            raise ValueError("Záloha používá nepodporovaný typ hodnoty registru.")
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _HKCU_RUN_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, kind, command)
        backup.pop(entry_id, None)
        _save_backup(backup)
        return f"Položka po startu byla obnovena: {name}."

    def _registry_entries(self) -> list[StartupEntry]:
        if winreg is None:
            return []
        keys = [
            (winreg.HKEY_CURRENT_USER, _HKCU_RUN_PATH, "HKCU Run", True),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run", False),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
                "HKLM WOW Run",
                False,
            ),
        ]
        entries: list[StartupEntry] = []
        for hive, path, source, can_disable in keys:
            try:
                with winreg.OpenKey(hive, path) as key:
                    for index in range(winreg.QueryInfoKey(key)[1]):
                        name, command, _kind = winreg.EnumValue(key, index)
                        entries.append(
                            StartupEntry(
                                id=_hkcu_run_id(str(name)) if source == "HKCU Run" else f"readonly:{source}:{index}",
                                name=str(name),
                                source=source,
                                command=str(command),
                                can_disable=can_disable,
                                recommendation=_recommendation_for_startup(str(name), str(command)),
                            )
                        )
            except OSError:
                continue
        return entries

    def _disabled_registry_entries(self, active_entries: list[StartupEntry]) -> list[StartupEntry]:
        active_ids = {entry.id for entry in active_entries}
        entries: list[StartupEntry] = []
        for entry_id, payload in _load_backup().items():
            if entry_id in active_ids:
                continue
            entries.append(
                StartupEntry(
                    id=entry_id,
                    name=str(payload.get("name", entry_id)),
                    source="HKCU Run (vypnuto ToolKitem)",
                    command=str(payload.get("command", "")),
                    recommendation="Lze obnovit zpět",
                    risk="safe",
                    enabled=False,
                    can_enable=True,
                )
            )
        return entries

    def _startup_folder_entries(self) -> list[StartupEntry]:
        folders = [
            Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup",
            Path(os.environ.get("PROGRAMDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup",
        ]
        entries: list[StartupEntry] = []
        for folder in folders:
            if not folder.exists():
                continue
            for item in folder.iterdir():
                if item.is_file():
                    entries.append(
                        StartupEntry(
                            id=f"folder:{quote(str(item), safe='')}",
                            name=item.name,
                            source=str(folder),
                            command=str(item),
                            recommendation="Vypnutí přes soubor ve složce Startup bude přidané v dalším průchodu",
                        )
                    )
        return entries


def _hkcu_run_id(name: str) -> str:
    return f"registry:hkcu_run:{quote(name, safe='')}"


def _decode_hkcu_run_id(entry_id: str) -> str | None:
    prefix = "registry:hkcu_run:"
    if not entry_id.startswith(prefix):
        return None
    return unquote(entry_id[len(prefix) :])


def _load_backup() -> dict[str, dict[str, object]]:
    if not _BACKUP_FILE.exists():
        return {}
    try:
        data = json.loads(_BACKUP_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): value for key, value in data.items() if isinstance(value, dict)}


def _save_backup(data: dict[str, dict[str, object]]) -> None:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    _BACKUP_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _assert_startup_entry_is_safe_to_disable(name: str, command: str) -> None:
    haystack = f"{name} {command}".lower()
    if any(word in haystack for word in _PROTECTED_STARTUP_WORDS):
        raise ValueError("Bezpečnostní položky Windows se z ToolKitu nevypínají.")


def _recommendation_for_startup(name: str, command: str) -> str:
    haystack = f"{name} {command}".lower()
    if any(word in haystack for word in ("steam", "discord", "teams", "onedrive", "spotify", "opera", "chrome")):
        return "Může zpomalovat start; vypnout jen pokud ji zákazník nepotřebuje hned po spuštění."
    return "Zkontrolovat ručně"
