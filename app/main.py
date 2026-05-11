from __future__ import annotations

import argparse
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config import AppConfig
from app.constants import ASSETS_DIR, ensure_local_directories
from app.logging_setup import configure_logging
from app.ui.main_window import MainWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cingy.Tech ToolKit")
    parser.add_argument("--smoke-test", action="store_true", help="Instantiate the app and exit without showing UI.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    ensure_local_directories()
    configure_logging()

    app = QApplication(sys.argv[:1])
    icon = ASSETS_DIR / "icon.ico"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))

    window = MainWindow(AppConfig.load())
    if args.smoke_test:
        return 0
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
