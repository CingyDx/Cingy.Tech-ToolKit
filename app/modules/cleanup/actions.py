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
        return 0, [f"Refused to clean unsafe path: {path}"]

    deleted_bytes = 0
    warnings: list[str] = []
    for child in path.iterdir() if path.exists() else []:
        try:
            is_junction = getattr(child, "is_junction", lambda: False)
            if child.is_symlink() or is_junction():
                warnings.append(f"Skipped reparse point or symlink: {child.name}")
                continue
            if child.is_dir():
                deleted_bytes += estimate_directory_size(child)
                shutil.rmtree(child, ignore_errors=True)
            else:
                deleted_bytes += child.stat().st_size
                child.unlink(missing_ok=True)
        except OSError as exc:
            warnings.append(f"Skipped locked item {child.name}: {exc}")
    return deleted_bytes, warnings


def _temp_action(action_id: str, title: str, path: Path, requires_admin: bool, risk: str) -> Action:
    def preview(_context):
        size = estimate_directory_size(path)
        return ActionPreview(
            action_id=action_id,
            summary=f"{title}: estimated {_format_bytes(size)} eligible for cleanup.",
            details=[str(path)],
            estimated_bytes=size,
        )

    def execute(_context):
        deleted, warnings = _delete_temp_contents(path)
        return ActionResult(
            action_id=action_id,
            success=not warnings,
            message=f"Cleaned approximately {_format_bytes(deleted)} from {path}.",
            stderr="\n".join(warnings),
        )

    return Action(
        id=action_id,
        title=title,
        category="Cleanup",
        description=f"Clean files from {path}. Locked files are skipped.",
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
            summary=f"{title}: preview-only MVP action.",
            details=[description],
            warnings=["Execution will be implemented with a dedicated safe backend in a later pass."],
        ),
        selected_by_default=False,
    )


def get_cleanup_actions() -> list[Action]:
    actions = [
        _temp_action(
            "cleanup.user_temp",
            "Clean user temp files",
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
                "Clean Windows temp files",
                Path(windir) / "Temp",
                requires_admin=True,
                risk="moderate",
            )
        )
    actions.extend(
        [
            _placeholder_cleanup_action(
                "cleanup.recycle_bin",
                "Empty recycle bin",
                "Requires final customer confirmation before emptying the recycle bin.",
                "moderate",
            ),
            _placeholder_cleanup_action(
                "cleanup.thumbnail_cache",
                "Clean thumbnail cache",
                "Will use a safe Explorer thumbnail cache reset flow in a later pass.",
                "moderate",
            ),
            _placeholder_cleanup_action(
                "cleanup.directx_shader_cache",
                "Clean DirectX shader cache",
                "Will use known DirectX cache locations only after preview.",
                "moderate",
            ),
            _placeholder_cleanup_action(
                "cleanup.delivery_optimization",
                "Clean Delivery Optimization cache",
                "Will use supported Windows cleanup mechanisms rather than deleting active update folders.",
                "moderate",
            ),
            _placeholder_cleanup_action(
                "cleanup.downloads_report",
                "Report large Downloads files",
                "Reports large files in Downloads without deleting anything.",
                "safe",
            ),
        ]
    )
    if not is_windows():
        for action in actions:
            action.description += " Non-Windows development environment detected."
    return actions
