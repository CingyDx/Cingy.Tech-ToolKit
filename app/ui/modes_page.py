from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.admin import is_running_as_admin
from app.core.action_engine import ActionEngine
from app.core.action_model import Action, ActionContext
from app.core.modes import ModeCatalog, ModeDefinition, ModePlan, build_mode_plan, friendly_action_title
from app.ui.components import (
    ActionChecklist,
    ActionSummaryPanel,
    EmptyState,
    ModeCard,
    SectionCard,
    button_row,
    make_scroll_area,
    page_header,
    primary_button,
    secondary_button,
)
from app.ui.workers import ActionWorker


class ModesPage(QWidget):
    def __init__(self, catalog: ModeCatalog) -> None:
        super().__init__()
        self.catalog = catalog
        self.stack = QStackedWidget()
        self.overview = self._build_overview()
        self.detail = ModeDetailPage(catalog)
        self.detail.back_requested.connect(lambda: self.stack.setCurrentWidget(self.overview))
        self.stack.addWidget(self.overview)
        self.stack.addWidget(self.detail)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    def show_mode(self, mode_id: str) -> None:
        self.detail.show_mode(mode_id)
        self.stack.setCurrentWidget(self.detail)

    def _build_overview(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(20)
        layout.addWidget(page_header("Režimy", "Vyber, co chceš s počítačem udělat. Detaily a potvrzení jsou až v dalším kroku."))

        differences = SectionCard("Jak se režimy liší")
        for line in [
            "Bezpečné vyčištění: uklidí jen bezpečné dočasné soubory, bez osobních dat.",
            "Zrychlit počítač: zkontroluje startup, bloatware a nastavení výkonu; odebrání je ruční.",
            "Herní režim: kontroluje herní nastavení, napájení a aplikace na pozadí; bez FPS hacků.",
            "Škola / práce: doporučí běžné aplikace a pořádek pro dokumenty a videohovory.",
            "Opravit Windows: servisní nástroje jako SFC, DISM a síťové opravy, spíš pro technika.",
            "Vlastní a Expert: ruční výběr, registry a detailní servis až po potvrzení.",
        ]:
            label = QLabel(line)
            label.setObjectName("MutedText")
            label.setWordWrap(True)
            differences.layout.addWidget(label)
        layout.addWidget(differences)

        grid = QWidget()
        from PySide6.QtWidgets import QGridLayout

        grid_layout = QGridLayout(grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(18)
        grid_layout.setVerticalSpacing(18)
        for index, mode in enumerate(self.catalog.visible_modes(include_technician=True)):
            card = ModeCard(mode)
            card.selected.connect(self.show_mode)
            grid_layout.addWidget(card, index // 2, index % 2)
        layout.addWidget(grid)
        layout.addStretch(1)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(make_scroll_area(content))
        return wrapper


class ModeDetailPage(QWidget):
    back_requested = Signal()

    def __init__(self, catalog: ModeCatalog) -> None:
        super().__init__()
        self.catalog = catalog
        self.mode: ModeDefinition | None = None
        self.plan: ModePlan | None = None
        self.group_checklists: list[ActionChecklist] = []
        self._thread: QThread | None = None
        self._worker: ActionWorker | None = None
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.addWidget(EmptyState("Vyber režim", "Nejdřív vyber režim na předchozí obrazovce."))

    def show_mode(self, mode_id: str) -> None:
        self.mode = self.catalog.get(mode_id)
        self.plan = build_mode_plan(self.mode, is_admin=is_running_as_admin())
        self._rebuild()

    def _rebuild(self) -> None:
        self._clear()
        assert self.mode is not None
        assert self.plan is not None
        self.group_checklists = []

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(20)
        layout.addWidget(page_header(self.mode.title_cs, self.mode.long_description_cs))

        back_top = secondary_button("← Zpět na výběr režimu")
        back_top.clicked.connect(self.back_requested.emit)
        layout.addWidget(button_row(back_top))

        summary = ActionSummaryPanel()
        summary.set_counts(
            total=self.plan.total_actions,
            admin=self.plan.requires_admin_count,
            risky=self.plan.risky_count,
            advanced=self.plan.advanced_count,
        )
        layout.addWidget(summary)

        checklist = SectionCard("Co tento režim udělá")
        for item in self.mode.checklist:
            checklist.layout.addWidget(QLabel(f"✓ {item}"))
        layout.addWidget(checklist)

        never = SectionCard("Co tento režim nikdy neudělá")
        for item in self.mode.never_does:
            never.layout.addWidget(QLabel(f"• {item}"))
        layout.addWidget(never)

        default_selected_ids = {action.id for action in self.plan.default_selected_actions}
        for title, actions in self._group_actions(self.plan.actions):
            if not actions:
                continue
            section = SectionCard(title)
            action_list = ActionChecklist(
                actions,
                unchecked_admin_when_not_admin=not is_running_as_admin(),
                default_selected_ids=default_selected_ids,
            )
            self.group_checklists.append(action_list)
            section.layout.addWidget(action_list)
            layout.addWidget(section)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("TechnicalOutput")
        self.output.setPlaceholderText("Technické detaily jsou skryté. Náhled plánu je zobrazí přehledně.")

        preview = primary_button("Náhled plánu")
        preview.clicked.connect(self.preview_plan)
        execute = primary_button("Spustit vybrané")
        execute.clicked.connect(self.execute_selected)
        back = secondary_button("Zpět na režimy")
        back.clicked.connect(self.back_requested.emit)
        layout.addWidget(button_row(preview, execute, back))
        layout.addWidget(self.output)
        layout.addStretch(1)
        self.root_layout.addWidget(make_scroll_area(content))

    def _clear(self) -> None:
        while self.root_layout.count():
            item = self.root_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def selected_actions(self) -> list[Action]:
        selected: list[Action] = []
        for checklist in self.group_checklists:
            selected.extend(checklist.selected_actions())
        return selected

    def preview_plan(self) -> None:
        actions = self.selected_actions()
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné akce.")
            return
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=True))
        previews = engine.preview_plan(actions)
        lines = ["Náhled plánu:", ""]
        for index, preview in enumerate(previews, 1):
            lines.append(f"{index}. {friendly_action_title(preview.action_id)}")
            lines.append(f"   {preview.summary}")
            for warning in preview.warnings:
                lines.append(f"   Pozor: {warning}")
        lines.extend(["", "Nic se nespustilo. Toto je pouze náhled."])
        self.output.setPlainText("\n".join(lines))

    def execute_selected(self) -> None:
        actions = self.selected_actions()
        if not actions:
            self.output.setPlainText("Zatím nebyly vybrané žádné akce.")
            return
        confirmed = QMessageBox.question(
            self,
            "Potvrdit spuštění",
            f"Spustit {len(actions)} vybraných akcí? Nic dalšího se nespustí.",
        )
        if confirmed != QMessageBox.Yes:
            return
        self._thread = QThread(self)
        engine = ActionEngine(ActionContext(is_admin=is_running_as_admin(), dry_run=False))
        self._worker = ActionWorker(engine, actions, confirmed=True)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.start()

    def _on_finished(self, results: list) -> None:
        lines = ["Dokončeno:", ""]
        lines.extend(f"- {result.message}" for result in results)
        lines.extend(["", "Na výběr jiného režimu se vrátíš tlačítkem „Zpět na režimy“."])
        self.output.setPlainText("\n".join(lines))

    def _on_failed(self, message: str) -> None:
        self.output.setPlainText(f"Akce nebyla spuštěna:\n{message}")

    def _group_actions(self, actions: list[Action]) -> list[tuple[str, list[Action]]]:
        safe = [action for action in actions if action.risk_level == "safe" and not action.requires_admin]
        optional = [action for action in actions if action.risk_level == "moderate" and not action.requires_admin]
        admin = [action for action in actions if action.requires_admin and action.risk_level not in {"risky", "expert"}]
        advanced = [action for action in actions if action.risk_level in {"risky", "expert"}]
        return [
            ("Bezpečné", safe),
            ("Volitelné", optional),
            ("Vyžaduje správce", admin),
            ("Pokročilé", advanced),
        ]
