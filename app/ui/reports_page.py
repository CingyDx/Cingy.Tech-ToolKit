from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.constants import REPORTS_DIR, SERVICE_CHECKLIST_ITEMS
from app.core.action_model import CustomerJobProfile, ServiceChecklistItem, SnapshotPair
from app.core.recommendations import recommendations_from_snapshot
from app.core.report_generator import ReportGenerator
from app.core.scanner import SystemScanner, summarize_system_snapshot
from app.ui.components import ReportList, SectionCard, button_row, make_scroll_area, page_header, primary_button, secondary_button


class ReportsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.customer = QLineEdit()
        self.device = QLineEdit()
        self.job = QLineEdit()
        self.problem = QLineEdit()
        self.price = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setMinimumHeight(110)
        self.checks = [QCheckBox(item) for item in SERVICE_CHECKLIST_ITEMS]
        self.report_list = ReportList()
        self.result = QLabel("Report zatím nebyl vytvořen.")
        self.result.setWordWrap(True)
        self.last_report_path: Path | None = None

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Reporty", "Servisní formulář pro zákazníka a technika."))
        layout.addWidget(self._customer_section())
        layout.addWidget(self._job_section())
        layout.addWidget(self._checklist_section())
        layout.addWidget(self._notes_section())

        generate = primary_button("Vygenerovat servisní report")
        generate.clicked.connect(self.generate_report)
        open_button = secondary_button("Otevřít report")
        open_button.clicked.connect(self.open_report)
        layout.addWidget(button_row(generate, open_button))
        layout.addWidget(self.result)

        recent = SectionCard("Vytvořené reporty")
        recent.layout.addWidget(self.report_list)
        layout.addWidget(recent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))
        self.refresh_reports()

    def _customer_section(self) -> QWidget:
        section = SectionCard("1. Zákazník")
        form = QFormLayout()
        form.addRow("Jméno zákazníka:", self.customer)
        form.addRow("Zařízení:", self.device)
        section.layout.addLayout(form)
        return section

    def _job_section(self) -> QWidget:
        section = SectionCard("2. Problém / zakázka")
        form = QFormLayout()
        form.addRow("Zakázka:", self.job)
        form.addRow("Problém:", self.problem)
        form.addRow("Cena:", self.price)
        section.layout.addLayout(form)
        return section

    def _checklist_section(self) -> QWidget:
        section = SectionCard("3. Servisní checklist")
        for check in self.checks:
            section.layout.addWidget(check)
        return section

    def _notes_section(self) -> QWidget:
        section = SectionCard("4. Poznámky technika")
        section.layout.addWidget(self.notes)
        return section

    def generate_report(self) -> None:
        customer = CustomerJobProfile(
            customer_name=self.customer.text(),
            device=self.device.text(),
            job=self.job.text(),
            problem=self.problem.text(),
            price=self.price.text(),
            notes=self.notes.toPlainText(),
        )
        checklist = [ServiceChecklistItem(label=check.text(), checked=check.isChecked()) for check in self.checks]
        system_snapshot = SystemScanner().scan()
        snapshot = SnapshotPair(
            before={
                "Disk C": f"{system_snapshot.get('system_drive_used_percent', '?')} % plný",
                "Startup": f"{system_snapshot.get('startup_item_count', 0)} položek",
                "Bloatware": f"{system_snapshot.get('detected_bloatware_count', 0)} nalezených položek",
                "Health score": system_snapshot.get("health_score", "?"),
            }
        )
        self.last_report_path = ReportGenerator().generate(
            customer=customer,
            snapshot=snapshot,
            system_info=summarize_system_snapshot(system_snapshot),
            recommendations=recommendations_from_snapshot(system_snapshot),
            checklist=checklist,
            technician_notes=self.notes.toPlainText(),
        )
        self.result.setText(f"Report vytvořen: {self.last_report_path}")
        self.refresh_reports()

    def open_report(self) -> None:
        if not self.last_report_path or not self.last_report_path.exists():
            self.result.setText("Report zatím nebyl vytvořen.")
            return
        try:
            os.startfile(self.last_report_path)  # type: ignore[attr-defined]
        except OSError as exc:
            self.result.setText(f"Report se nepodařilo otevřít: {exc}")

    def refresh_reports(self) -> None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        paths = sorted(str(path) for path in REPORTS_DIR.glob("*.html"))
        self.report_list.set_paths(paths)
