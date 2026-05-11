from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.constants import REPORTS_DIR, SERVICE_CHECKLIST_ITEMS
from app.core.action_model import CustomerJobProfile, ServiceChecklistItem
from app.core.report_generator import ReportGenerator
from app.ui.components import ReportList, page_header


class ReportsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.customer = QLineEdit()
        self.device = QLineEdit()
        self.job = QLineEdit()
        self.problem = QLineEdit()
        self.price = QLineEdit()
        self.notes = QTextEdit()
        self.checks = [QCheckBox(item) for item in SERVICE_CHECKLIST_ITEMS]
        self.report_list = ReportList()

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.addRow("Jméno zákazníka:", self.customer)
        form.addRow("Zařízení:", self.device)
        form.addRow("Zakázka:", self.job)
        form.addRow("Problém:", self.problem)
        form.addRow("Cena:", self.price)
        form.addRow("Poznámky:", self.notes)

        generate = QPushButton("Generate HTML Report")
        generate.clicked.connect(self.generate_report)
        layout = QVBoxLayout(self)
        layout.addWidget(page_header("Reports", "Customer/job fields, checklist, and local HTML reports."))
        layout.addWidget(form_widget)
        for check in self.checks:
            layout.addWidget(check)
        layout.addWidget(generate)
        layout.addWidget(self.report_list, 1)
        self.refresh_reports()

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
        ReportGenerator().generate(customer=customer, checklist=checklist, technician_notes=self.notes.toPlainText())
        self.refresh_reports()

    def refresh_reports(self) -> None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        paths = sorted(str(path) for path in REPORTS_DIR.glob("*.html"))
        self.report_list.set_paths(paths)
