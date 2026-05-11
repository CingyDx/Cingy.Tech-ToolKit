from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from app.admin import is_windows
from app.core.action_model import Action, ActionPreview, ActionResult
from app.core.scanner import estimate_directory_size


def _format_bytes(value: int) -> str:
    if value >= 1024**3:
        return f"{value / (1024**3):.1f} GB"
    if value >= 1024**2:
        return f"{value / (1024**2):.1f} MB"
    return f"{value / 1024:.1f} KB"


def _safe_temp_path(path: Path) -> bool:
    resolved = path.resolve()
    temp_roots = [Path(tempfile.gettempdir()).resolve()]
    windir = os.environ.get("WINDIR")
    if windir:
        temp_roots.append((Path(windir) / "Temp").resolve())
    return any(resolved == root or root in resolved.parents for root in temp_roots)


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
    actions = [
        _temp_action(
            "cleanup.user_temp",
            "Vyčištění uživatelských dočasných souborů",
            Path(tempfile.gettempdir()),
            requires_admin=False,
            risk="safe",
        )
    ]
    windir = os.environ.get("WINDIR")
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
            _placeholder_cleanup_action(
                "cleanup.recycle_bin",
                "Vysypání koše po potvrzení",
                "Před vysypáním koše bude potřeba finální potvrzení zákazníka.",
                "moderate",
            ),
            _placeholder_cleanup_action(
                "cleanup.thumbnail_cache",
                "Vyčištění náhledů obrázků",
                "V dalším průchodu použije bezpečný postup pro reset náhledů Průzkumníka.",
                "moderate",
            ),
            _placeholder_cleanup_action(
                "cleanup.directx_shader_cache",
                "Vyčištění DirectX cache",
                "Použije jen známé cache DirectX po předchozím náhledu.",
                "moderate",
            ),
            _placeholder_cleanup_action(
                "cleanup.delivery_optimization",
                "Vyčištění cache aktualizací",
                "Použije podporované mechanismy Windows místo mazání aktivních složek aktualizací.",
                "moderate",
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
