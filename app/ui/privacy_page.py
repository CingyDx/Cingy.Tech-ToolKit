from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import ActionContext
from app.modules.privacy import load_privacy_toggles, privacy_toggle_actions
from app.ui.components import ActionChecklist, SectionCard, button_row, make_scroll_area, page_header, primary_button, secondary_button


class PrivacyPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.actions = privacy_toggle_actions()
        self.checklist = ActionChecklist(self.actions, default_selected_ids=set())
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nastavení", "Riziko", "Správce", "Popis", "Registr"])
        self.table.hide()
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        preview = primary_button("Náhled vybraných")
        preview.clicked.connect(self.preview)
        execute = primary_button("Použít vybrané")
        execute.clicked.connect(self.execute)
        toggle = secondary_button("Zobrazit technické detaily")
        toggle.clicked.connect(self.toggle_table)
        self.toggle = toggle

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Soukromí a nastavení Windows", "Bezpečné uživatelské přepínače. Každá změna má náhled a zálohu."))
        card = SectionCard("Bezpečné přepínače")
        card.layout.addWidget(self.checklist)
        layout.addWidget(card)
        layout.addWidget(button_row(preview, execute, toggle))
        layout.addWidget(self.table)
        layout.addWidget(self.output, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))
        self.populate()

    def toggle_table(self) -> None:
        visible = not self.table.isVisible()
        self.table.setVisible(visible)
        self.toggle.setText("Skrýt technické detaily" if visible else "Zobrazit technické detaily")

    def populate(self) -> None:
        toggles = load_privacy_toggles()
        self.table.setRowCount(len(toggles))
        for row, toggle in enumerate(toggles):
            registry = toggle.get("registry") if isinstance(toggle.get("registry"), dict) else {}
            values = [
                toggle.get("title", ""),
                toggle.get("risk", ""),
                "Ano" if toggle.get("requires_admin") else "Ne",
                toggle.get("description", ""),
                f"{registry.get('hive', '')}\\{registry.get('path', '')}\\{registry.get('value_name', '')}" if registry else "Pouze přehled",
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def preview(self) -> None:
        actions = self.checklist.selected_actions()
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné přepínače.")
            return
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=True))
        previews = engine.preview_plan(actions)
        lines: list[str] = ["Náhled nastavení:"]
        for preview in previews:
            lines.append(f"- {preview.summary}")
            for detail in preview.details:
                lines.append(f"  {detail}")
        self.output.setPlainText("\n".join(lines))

    def execute(self) -> None:
        actions = self.checklist.selected_actions()
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné přepínače.")
            return
        confirmed = QMessageBox.question(
            self,
            "Potvrdit změny nastavení",
            f"Použít {len(actions)} vybraných bezpečných nastavení? Před změnou se uloží záloha.",
        )
        if confirmed != QMessageBox.Yes:
            return
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=False))
        try:
            results = engine.execute_plan(actions, confirmed=True)
        except Exception as exc:
            self.output.setPlainText(str(exc))
            return
        self.output.setPlainText("\n".join(f"- {result.message}" for result in results))
