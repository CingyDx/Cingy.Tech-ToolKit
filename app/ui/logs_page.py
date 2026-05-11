from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.constants import LOGS_DIR
from app.ui.components import EmptyState, SectionCard, button_row, make_scroll_area, page_header, secondary_button


class LogsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        refresh = secondary_button("Obnovit logy")
        refresh.clicked.connect(self.refresh)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 30)
        layout.setSpacing(18)
        layout.addWidget(page_header("Logy", "Technické záznamy akcí. Zákazník je běžně nepotřebuje vidět."))
        layout.addWidget(button_row(refresh))
        layout.addWidget(self.output, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scroll_area(content))
        self.refresh()

    def refresh(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(LOGS_DIR.glob("*.log")) + sorted(LOGS_DIR.glob("*.jsonl"))
        if not files:
            self.output.setPlainText("Zatím nebyly vytvořené žádné technické logy.")
            return
        lines: list[str] = []
        for path in files[-5:]:
            lines.append(f"=== {path.name} ===")
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                content = f"Nelze přečíst log: {exc}"
            recent_lines = content.splitlines()[-40:]
            lines.append("\n".join(recent_lines))
            lines.append("")
        self.output.setPlainText("\n".join(lines))
