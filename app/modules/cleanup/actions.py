from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

from app.admin import is_windows
from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.scanner import estimate_directory_size


def _format_bytes(value: int) -> str:
    if value >= 1024**3:
        return f"{value / (1024**3):.1f} GB"
    if value >= 1024**2:
        return f"{value / (1024**2):.1f} MB"
    return f"{value / 1024:.1f} KB"


def is_safe_cleanup_path(path: Path, allowed_roots: Iterable[Path]) -> bool:
    try:
        resolved = path.resolve()
        roots = [root.resolve() for root in allowed_roots]
    except OSError:
        return False
    if resolved.name.lower() in {"downloads", "documents", "desktop", "pictures", "music", "videos"}:
        return False
    return any(resolved == root or root in resolved.parents for root in roots)


def get_thumbnail_cache_paths(local_app_data: Path) -> list[Path]:
    explorer = local_app_data / "Microsoft" / "Windows" / "Explorer"
    if not explorer.exists():
        return []
    paths = list(explorer.glob("thumbcache_*.db"))
    paths.extend(explorer.glob("iconcache_*.db"))
    return [path for path in paths if path.is_file()]


def _safe_temp_path(path: Path) -> bool:
    resolved = path.resolve()
    temp_roots = [Path(tempfile.gettempdir()).resolve()]
    windir = os.environ.get("WINDIR")
    if windir:
        temp_roots.append((Path(windir) / "Temp").resolve())
    return is_safe_cleanup_path(resolved, temp_roots)


def _delete_cache_contents(paths: Iterable[Path], allowed_roots: Iterable[Path]) -> tuple[int, list[str]]:
    deleted_bytes = 0
    warnings: list[str] = []
    roots = list(allowed_roots)
    for path in paths:
        if not path.exists():
            continue
        if not is_safe_cleanup_path(path, roots):
            warnings.append(f"Odmítnuto čištění mimo povolenou cache složku: {path}")
            continue
        child_paths = path.iterdir() if path.is_dir() else [path]
        for child in child_paths:
            try:
                is_junction = getattr(child, "is_junction", lambda: False)
                if child.is_symlink() or is_junction():
                    warnings.append(f"Přeskočen odkaz nebo junction: {child.name}")
                    continue
                if child.is_dir():
                    deleted_bytes += estimate_directory_size(child)
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    deleted_bytes += child.stat().st_size
                    child.unlink(missing_ok=True)
            except OSError as exc:
                warnings.append(f"Přeskočena zamčená položka {child.name}: {exc}")
    return deleted_bytes, warnings


def _delete_temp_contents(path: Path) -> tuple[int, list[str]]:
    if not _safe_temp_path(path):
        return 0, [f"Odmítnuto čištění mimo bezpečnou temp složku: {path}"]

    deleted_bytes = 0
    warnings: list[str] = []
    for child in path.iterdir() if path.exists() else []:
        try:
            is_junction = getattr(child, "is_junction", lambda: False)
            if child.is_symlink() or is_junction():
                warnings.append(f"Přeskočen odkaz nebo junction: {child.name}")
                continue
            if child.is_dir():
                deleted_bytes += estimate_directory_size(child)
                shutil.rmtree(child, ignore_errors=True)
            else:
                deleted_bytes += child.stat().st_size
                child.unlink(missing_ok=True)
        except OSError as exc:
            warnings.append(f"Přeskočena zamčená položka {child.name}: {exc}")
    return deleted_bytes, warnings


def _temp_action(action_id: str, title: str, path: Path, requires_admin: bool, risk: str) -> Action:
    def preview(_context):
        size = estimate_directory_size(path)
        return ActionPreview(
            action_id=action_id,
            summary=f"{title}: odhad {_format_bytes(size)} bezpečných položek k vyčištění.",
            details=[str(path)],
            estimated_bytes=size,
        )

    def execute(_context):
        deleted, warnings = _delete_temp_contents(path)
        return ActionResult(
            action_id=action_id,
            success=True,
            message=f"Vyčištěno přibližně {_format_bytes(deleted)} ze složky {path}. Zamčené položky se bezpečně přeskočily.",
            stderr="\n".join(warnings),
        )

    return Action(
        id=action_id,
        title=title,
        category="Cleanup",
        description=f"Vyčistí dočasné soubory ze složky {path}. Zamčené položky se přeskočí.",
        risk_level=risk,
        requires_admin=requires_admin,
        preview_handler=preview,
        execute_handler=execute,
        affected_paths=[str(path)],
        selected_by_default=(risk == "safe"),
    )


def _cache_cleanup_action(
    action_id: str,
    title: str,
    description: str,
    paths: list[Path],
    allowed_roots: list[Path],
    risk: str,
    *,
    requires_admin: bool = False,
) -> Action:
    def preview(_context):
        size = sum(estimate_directory_size(path) if path.is_dir() else path.stat().st_size for path in paths if path.exists())
        return ActionPreview(
            action_id=action_id,
            summary=f"{title}: odhad {_format_bytes(size)} bezpečných cache položek.",
            details=[str(path) for path in paths],
            estimated_bytes=size,
            warnings=[] if paths else ["Cíl není na tomto PC dostupný."],
        )

    def execute(_context):
        deleted, warnings = _delete_cache_contents(paths, allowed_roots)
        return ActionResult(
            action_id=action_id,
            success=True,
            message=f"{title}: vyčištěno přibližně {_format_bytes(deleted)}. Zamčené položky se přeskočily.",
            stderr="\n".join(warnings),
        )

    return Action(
        id=action_id,
        title=title,
        category="Cleanup",
        description=description,
        risk_level=risk,
        requires_admin=requires_admin,
        preview_handler=preview,
        execute_handler=execute,
        affected_paths=[str(path) for path in paths],
        selected_by_default=False,
    )


def _recycle_bin_action() -> Action:
    def execute(_context):
        if not is_windows():
            return ActionResult(
                action_id="cleanup.recycle_bin",
                success=True,
                skipped=True,
                message="Koš lze vysypat pouze ve Windows.",
            )
        try:
            import ctypes

            flags = 0x00000001 | 0x00000002 | 0x00000004
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        except Exception as exc:  # pragma: no cover - Windows shell API
            return ActionResult(action_id="cleanup.recycle_bin", success=False, message=f"Koš se nepodařilo vysypat: {exc}")
        return ActionResult(
            action_id="cleanup.recycle_bin",
            success=result == 0,
            message="Koš byl vysypán." if result == 0 else f"Koš se nepodařilo vysypat. Kód: {result}",
        )

    return Action(
        id="cleanup.recycle_bin",
        title="Vysypání koše po potvrzení",
        category="Cleanup",
        description="Vysype Koš přes Windows Shell API až po potvrzení.",
        risk_level="moderate",
        requires_admin=False,
        preview_handler=lambda _context: ActionPreview(
            action_id="cleanup.recycle_bin",
            summary="Koš bude vysypán přes podporované Windows API.",
            warnings=["Zkontroluj se zákazníkem, že v Koši není nic potřebného."],
        ),
        execute_handler=execute,
        selected_by_default=False,
    )


def _placeholder_cleanup_action(action_id: str, title: str, description: str, risk: str) -> Action:
    return Action(
        id=action_id,
        title=title,
        category="Cleanup",
        description=description,
        risk_level=risk,
        requires_admin=False,
        preview_handler=lambda _context: ActionPreview(
            action_id=action_id,
            summary=f"{title}: zatím jen bezpečný náhled v MVP.",
            details=[description],
            warnings=["Spuštění bude doplněné bezpečným backendem v dalším průchodu."],
        ),
        selected_by_default=False,
    )


def get_cleanup_actions() -> list[Action]:
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    windir = os.environ.get("WINDIR")
    actions = [
        _temp_action(
            "cleanup.user_temp",
            "Vyčištění uživatelských dočasných souborů",
            Path(tempfile.gettempdir()),
            requires_admin=False,
            risk="safe",
        )
    ]
    if windir:
        actions.append(
            _temp_action(
                "cleanup.windows_temp",
                "Vyčištění systémových dočasných souborů",
                Path(windir) / "Temp",
                requires_admin=True,
                risk="moderate",
            )
        )
    actions.extend(
        [
            _recycle_bin_action(),
            _cache_cleanup_action(
                "cleanup.thumbnail_cache",
                "Vyčištění náhledů obrázků",
                "Vyčistí cache náhledů Průzkumníka pro aktuálního uživatele.",
                get_thumbnail_cache_paths(local),
                [local / "Microsoft" / "Windows" / "Explorer"],
                "moderate",
            ),
            _cache_cleanup_action(
                "cleanup.directx_shader_cache",
                "Vyčištění DirectX cache",
                "Vyčistí známé shader cache složky pro aktuálního uživatele.",
                [
                    local / "D3DSCache",
                    local / "NVIDIA" / "DXCache",
                    local / "AMD" / "DxCache",
                ],
                [
                    local / "D3DSCache",
                    local / "NVIDIA" / "DXCache",
                    local / "AMD" / "DxCache",
                ],
                "moderate",
            ),
            _cache_cleanup_action(
                "cleanup.delivery_optimization",
                "Vyčištění cache aktualizací",
                "Vyčistí známou cache Delivery Optimization bez vypínání Windows Update.",
                [Path(windir or "") / "ServiceProfiles" / "NetworkService" / "AppData" / "Local" / "Microsoft" / "Windows" / "DeliveryOptimization" / "Cache"],
                [Path(windir or "") / "ServiceProfiles" / "NetworkService" / "AppData" / "Local" / "Microsoft" / "Windows" / "DeliveryOptimization" / "Cache"],
                "moderate",
                requires_admin=True,
            ),
            _placeholder_cleanup_action(
                "cleanup.downloads_report",
                "Přehled velkých souborů ve Stažených",
                "Pouze zobrazí velké soubory ve Stažených. Nic nemaže.",
                "safe",
            ),
        ]
    )
    if not is_windows():
        for action in actions:
            action.description += " Detekováno vývojové prostředí mimo Windows."
    return actions
