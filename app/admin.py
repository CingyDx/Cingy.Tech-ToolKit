from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path


def is_windows() -> bool:
    return os.name == "nt"


def is_running_as_admin() -> bool:
    if not is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def restart_as_admin() -> bool:
    """Prompt UAC and relaunch the current Python entrypoint as Administrator."""
    if not is_windows():
        return False

    executable = Path(sys.executable)
    args = " ".join(f'"{arg}"' for arg in sys.argv)
    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            str(executable),
            args,
            None,
            1,
        )
    except Exception:
        return False
    return int(result) > 32
