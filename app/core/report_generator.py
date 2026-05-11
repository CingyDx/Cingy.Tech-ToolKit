from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.constants import REPORTS_DIR, TEMPLATE_DIR, SERVICE_CHECKLIST_ITEMS
from app.core.action_model import CustomerJobProfile, ServiceChecklistItem, SnapshotPair


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


def default_checklist() -> list[ServiceChecklistItem]:
    return [ServiceChecklistItem(label=item) for item in SERVICE_CHECKLIST_ITEMS]


class ReportGenerator:
    def __init__(self, template_dir: Path | None = None, output_dir: Path | None = None) -> None:
        self.template_dir = template_dir or TEMPLATE_DIR
        self.output_dir = output_dir or REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def generate(
        self,
        *,
        customer: CustomerJobProfile | None = None,
        snapshot: SnapshotPair | None = None,
        system_info: dict[str, Any] | None = None,
        actions_performed: list[dict[str, Any]] | None = None,
        skipped_actions: list[dict[str, Any]] | None = None,
        warnings: list[str] | None = None,
        recommendations: list[str] | None = None,
        checklist: list[ServiceChecklistItem] | None = None,
        raw_logs: str = "",
        restart_required: bool = False,
        technician_notes: str = "",
    ) -> Path:
        template = self.env.get_template("service_report.html")
        created = datetime.now()
        html = template.render(
            generated_at=created.strftime("%Y-%m-%d %H:%M"),
            customer=_plain(customer or CustomerJobProfile()),
            snapshot=_plain(snapshot or SnapshotPair()),
            system_info=system_info or {},
            actions_performed=actions_performed or [],
            skipped_actions=skipped_actions or [],
            warnings=warnings or [],
            recommendations=recommendations or [],
            checklist=_plain(checklist or default_checklist()),
            raw_logs=raw_logs,
            restart_required=restart_required,
            technician_notes=technician_notes,
        )
        output = self.output_dir / f"service_report_{created.strftime('%Y%m%d_%H%M%S')}.html"
        output.write_text(html, encoding="utf-8")
        return output
