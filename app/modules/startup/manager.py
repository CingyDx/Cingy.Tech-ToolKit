from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None


@dataclass(slots=True)
class StartupEntry:
    name: str
    source: str
    command: str
    publisher: str = ""
    recommendation: str = "Review manually"
    risk: str = "moderate"


class StartupManager:
    def list_entries(self) -> list[StartupEntry]:
        entries = self._registry_entries()
        entries.extend(self._startup_folder_entries())
        return entries

    def _registry_entries(self) -> list[StartupEntry]:
        if winreg is None:
            return []
        keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM WOW Run"),
        ]
        entries: list[StartupEntry] = []
        for hive, path, source in keys:
            try:
                with winreg.OpenKey(hive, path) as key:
                    for index in range(winreg.QueryInfoKey(key)[1]):
                        name, command, _kind = winreg.EnumValue(key, index)
                        entries.append(StartupEntry(name=str(name), source=source, command=str(command)))
            except OSError:
                continue
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
                    entries.append(StartupEntry(name=item.name, source=str(folder), command=str(item)))
        return entries
