from __future__ import annotations

import os
import platform
import socket
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from app.admin import is_running_as_admin, is_windows
from app.constants import RULES_DIR
from app.core.score import calculate_health_score
from app.core.state_store import JsonRuleStore

try:
    import psutil
except ImportError:  # pragma: no cover - dependency is declared, fallback keeps imports safe.
    psutil = None

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows fallback.
    winreg = None


def estimate_directory_size(path: str | Path, *, max_files: int = 25_000) -> int:
    root = Path(path)
    if not root.exists() or not root.is_dir():
        return 0

    total = 0
    scanned = 0
    for current_root, _dirs, files in os.walk(root, topdown=True):
        for filename in files:
            if scanned >= max_files:
                return total
            scanned += 1
            file_path = Path(current_root) / filename
            try:
                total += file_path.stat().st_size
            except OSError:
                continue
    return total


def _bytes_to_gb(value: int) -> float:
    return round(value / (1024**3), 1)


def _windows_version() -> str:
    release = platform.release()
    version = platform.version()
    edition = platform.platform()
    return f"{edition} ({release}, build {version})"


def _cpu_name() -> str:
    if psutil:
        return platform.processor() or "Unknown CPU"
    return platform.processor() or "Unknown CPU"


def _ram_info() -> tuple[float, int]:
    if not psutil:
        return 0.0, 0
    mem = psutil.virtual_memory()
    return _bytes_to_gb(mem.total), int(mem.percent)


def _disk_info() -> list[dict[str, Any]]:
    if not psutil:
        return []
    disks: list[dict[str, Any]] = []
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except OSError:
            continue
        disks.append(
            {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total_gb": _bytes_to_gb(usage.total),
                "free_gb": _bytes_to_gb(usage.free),
                "used_percent": int(usage.percent),
            }
        )
    return disks


def _count_registry_uninstall_apps() -> int:
    if not is_windows() or winreg is None:
        return 0
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    count = 0
    for hive, path in roots:
        try:
            with winreg.OpenKey(hive, path) as key:
                for index in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            winreg.QueryValueEx(subkey, "DisplayName")
                            count += 1
                    except OSError:
                        continue
        except OSError:
            continue
    return count


def _count_startup_items() -> int:
    count = 0
    startup_folders = [
        Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup",
        Path(os.environ.get("PROGRAMDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup",
    ]
    for folder in startup_folders:
        if folder.exists():
            count += len([path for path in folder.iterdir() if path.is_file()])

    if is_windows() and winreg is not None:
        keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for hive, path in keys:
            try:
                with winreg.OpenKey(hive, path) as key:
                    count += winreg.QueryInfoKey(key)[1]
            except OSError:
                continue
    return count


def _estimate_temp_cache() -> int:
    paths = [Path(tempfile.gettempdir())]
    windir = os.environ.get("WINDIR")
    if windir:
        paths.append(Path(windir) / "Temp")
    return sum(estimate_directory_size(path) for path in paths)


def _detected_bloatware_count() -> int:
    try:
        rules = JsonRuleStore(RULES_DIR).load_required("bloatware_rules.json").get("rules", [])
    except Exception:
        return 0
    installed_names = _installed_app_names()
    count = 0
    for rule in rules:
        patterns = [pattern.lower() for pattern in rule.get("match_patterns", [])]
        if any(pattern in app for app in installed_names for pattern in patterns):
            count += 1
    return count


def _installed_app_names() -> list[str]:
    if not is_windows() or winreg is None:
        return []
    names: list[str] = []
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, path in roots:
        try:
            with winreg.OpenKey(hive, path) as key:
                for index in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            name, _kind = winreg.QueryValueEx(subkey, "DisplayName")
                            names.append(str(name).lower())
                    except OSError:
                        continue
        except OSError:
            continue
    return names


def scan_system() -> dict[str, Any]:
    ram_total, ram_percent = _ram_info()
    disks = _disk_info()
    system_drive = disks[0] if disks else {"used_percent": 0}
    snapshot: dict[str, Any] = {
        "device_name": socket.gethostname(),
        "windows_version": _windows_version(),
        "cpu": _cpu_name(),
        "ram_total_gb": ram_total,
        "ram_used_percent": ram_percent,
        "gpu": "Unknown",
        "disks": disks,
        "system_drive_used_percent": int(system_drive.get("used_percent", 0)),
        "system_drive_health": "Unknown",
        "boot_drive_type": "unknown",
        "installed_app_count": _count_registry_uninstall_apps(),
        "startup_item_count": _count_startup_items(),
        "detected_bloatware_count": _detected_bloatware_count(),
        "temp_cache_estimated_bytes": _estimate_temp_cache(),
        "windows_activation_status": "Not checked in MVP",
        "windows_update_status": "Not checked in MVP",
        "admin_status": is_running_as_admin(),
        "last_scan_time": datetime.now().isoformat(timespec="seconds"),
        "repair_warning_count": 0,
    }
    health = calculate_health_score(snapshot)
    snapshot["health_score"] = health.score
    snapshot["health_explanations"] = health.explanations
    snapshot["health_factors"] = health.factors
    return snapshot


def summarize_system_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "device_name",
        "windows_version",
        "cpu",
        "ram_total_gb",
        "gpu",
        "admin_status",
        "health_score",
    )
    return {key: snapshot.get(key) for key in keys}


class SystemScanner:
    def scan(self) -> dict[str, Any]:
        return scan_system()
