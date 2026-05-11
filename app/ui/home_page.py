from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.admin import is_running_as_admin
from app.config import AppConfig
from app.constants import APP_NAME, APP_SUBTITLE, REPORTS_DIR
from app.core.modes import ModeCatalog
from app.core.scanner import SystemScanner
from app.ui.components import (
    ModeCard,
    SectionCard,
    StatusPill,
    make_scroll_area,
    page_header,
    primary_button,
)


class HomePage(QWidget):
    mode_selected = Signal(str)
    scan_requested = Signal()

    def __init__(self, scanner: SystemScanner, config: AppConfig, catalog: ModeCatalog) -> None:
        super().__init__()
        self.scanner = scanner
        self.config = config
        self.catalog = catalog
        self.snapshot: dict[str, object] | None = None

        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(30, 28, 30, 30)
        self.layout.setSpacing(22)
        self._build()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))

    def _build(self) -> None:
        hero = SectionCard(APP_NAME, "Vyber režim opravy nebo optimalizace", accent=True)
        brand = QLabel(APP_SUBTITLE)
        brand.setObjectName("HeroSubtitle")
        tech = QLabel(f"Technik: {self.config.technician_name}")
        tech.setObjectName("MutedText")
        cta = primary_button("Spustit rychlou kontrolu")
        cta.clicked.connect(self._run_quick_scan)
        hero.layout.addWidget(brand)
        hero.layout.addWidget(tech)
        hero.layout.addWidget(cta)
        self.layout.addWidget(hero)

        self.status_grid = QGridLayout()
        self.status_grid.setHorizontalSpacing(16)
        self.status_grid.setVerticalSpacing(16)
        self.layout.addLayout(self.status_grid)
        self._refresh_status_cards()

        safety = SectionCard("Bezpečný servisní postup")
        for line in (
            "Nic se nespustí bez potvrzení.",
            "Osobní soubory se nemažou.",
            "Pokročilé akce jsou skryté pro technika.",
        ):
            safety.layout.addWidget(StatusPill(line, "good"))
        self.layout.addWidget(safety)

        self.layout.addWidget(page_header("Režimy", "Vyber jednoduchý režim. Technické detaily uvidíš až po otevření plánu."))
        mode_grid = QWidget()
        grid = QGridLayout(mode_grid)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        for index, mode in enumerate(self.catalog.visible_modes(include_technician=True)):
            card = ModeCard(mode)
            card.selected.connect(self.mode_selected.emit)
            grid.addWidget(card, index // 2, index % 2)
        self.layout.addWidget(mode_grid)

        self.recent_card = SectionCard("Poslední report")
        self._refresh_recent_report()
        self.layout.addWidget(self.recent_card)
        self.layout.addStretch(1)

    def _run_quick_scan(self) -> None:
        self.snapshot = self.scanner.scan()
        self._refresh_status_cards()
        self.scan_requested.emit()

    def _refresh_status_cards(self) -> None:
        while self.status_grid.count():
            item = self.status_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        health = "Neznámé"
        last_scan = "Ještě neproběhla"
        disk = "Nejdřív spusť kontrolu PC."
        tone = "neutral"
        if self.snapshot:
            health = f"{self.snapshot.get('health_score', '?')}/100"
            last_scan = str(self.snapshot.get("last_scan_time", "Teď"))
            used = int(self.snapshot.get("system_drive_used_percent", 0) or 0)
            disk = f"Systémový disk je zaplněný na {used}%."
            tone = "warn" if used >= 85 else "good"

        cards = [
            ("Správce", "Ano" if is_running_as_admin() else "Ne", "good" if is_running_as_admin() else "warn"),
            ("Poslední kontrola", last_scan, "neutral"),
            ("Stav počítače", health, "good" if health != "Neznámé" else "neutral"),
            ("Místo na disku", disk, tone),
        ]
        for index, (title, value, card_tone) in enumerate(cards):
            card = SectionCard(title)
            card.layout.addWidget(StatusPill(value, card_tone))
            self.status_grid.addWidget(card, index // 2, index % 2)

    def _refresh_recent_report(self) -> None:
        reports = sorted(REPORTS_DIR.glob("*.html"), key=lambda path: path.stat().st_mtime if path.exists() else 0)
        text = str(reports[-1]) if reports else "Report zatím nebyl vytvořen."
        self.recent_card.layout.addWidget(QLabel(text))
