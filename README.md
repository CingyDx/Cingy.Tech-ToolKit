# Cingy.Tech ToolKit

**Windows Optimizer & Service Suite** for professional PC repair and optimization work.

This MVP is a safe foundation for a technician-facing Windows toolkit. It is not a one-click booster and it does not apply hidden changes. Every system-changing operation is represented as an `Action` with preview, risk level, admin requirement, execution result, and logging.

## Current MVP

- PySide6 desktop shell with Dashboard, Scan, Cleanup, Debloat, Startup, Power, Repair, Privacy, Expert Lab, Custom Mode, Reports, and Settings pages.
- Administrator detection with a visible warning and explicit “Restart as Administrator” button.
- Central action engine with dry-run preview, confirmation gate, admin gate, risky/expert gate, and JSONL session logs.
- System scanner using `psutil` where available.
- Transparent health score based on disk fullness, startup count, bloatware count, RAM pressure, repair warnings, and temp/cache size.
- Safe cleanup preview and a limited current-user temp cleanup executor.
- Restore point wrapper through PowerShell.
- Repair action wrappers for SFC, DISM, CHKDSK, DNS flush, Winsock reset, and IP stack reset.
- Rule-backed presets, bloatware rules, startup rules, cleanup rules, power profiles, privacy toggles, install packs, and expert registry tweak metadata.
- HTML service report generation with customer/job fields, checklist, before/after snapshots, actions, warnings, recommendations, and raw logs.

## Requirements

- Windows 10/11 for full functionality.
- Python 3.11+.
- PowerShell available on the system.

## Setup

```powershell
cd C:\Users\kryst\Desktop\Cingy.Tech-ToolKit
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `python` is not on PATH, install Python 3.11+ or use the bundled Codex runtime only for local development checks.

## Run

```powershell
.\scripts\run_dev.ps1
```

Or:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Local Outputs

- Logs: `logs/`
- Reports: `reports/`
- Backups: `backups/`

These folders are designed for future portable packaging as:

```text
CingyTechToolKit_Portable.exe
logs/
reports/
backups/
```

## Important Safety Notes

The toolkit does not disable Microsoft Defender, does not disable Windows Update completely, does not remove Microsoft Edge forcibly, does not clean Downloads by default, and does not run PowerShell built from unsanitized user input.

See [SAFETY.md](SAFETY.md) for the full safety model.
