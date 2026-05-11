from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from app.core.safety import assert_safe_powershell_script


@dataclass(slots=True)
class PowerShellResult:
    returncode: int
    stdout: str
    stderr: str
    command_preview: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class PowerShellRunner:
    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("powershell.exe") or shutil.which("pwsh.exe")

    def is_available(self) -> bool:
        return bool(self.executable)

    def preview(self, script: str) -> str:
        assert_safe_powershell_script(script)
        exe = self.executable or "powershell.exe"
        return f'{exe} -NoProfile -NonInteractive -Command "{script}"'

    def run(self, script: str, *, timeout: int = 900) -> PowerShellResult:
        assert_safe_powershell_script(script)
        command_preview = self.preview(script)
        if not self.executable:
            return PowerShellResult(127, "", "PowerShell executable was not found.", command_preview)

        completed = subprocess.run(
            [self.executable, "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return PowerShellResult(
            completed.returncode,
            completed.stdout,
            completed.stderr,
            command_preview,
        )
