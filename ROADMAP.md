# Roadmap

## Next Pass

- Add richer Dashboard hardware detection: GPU, SSD/HDD/NVMe, SMART/disk health where safely available.
- Implement Windows activation and Windows Update status checks using safe read-only mechanisms.
- Expand cleanup executors for Recycle Bin, thumbnail cache, DirectX shader cache, and Delivery Optimization through supported APIs or well-scoped PowerShell.
- Add browser cache cleanup with explicit browser selection and warnings.
- Add before/after snapshot capture around action execution.
- Add report recommendations from scanner facts.

## Debloat

- Add AppX package detection.
- Add final confirmation summary for selected removals.
- Add undo/backup notes for each supported uninstall method.
- Keep OneDrive and Microsoft framework packages protected unless explicitly selected with clear warnings.

## Startup Manager

- Add disable/enable implementation with reversible backups.
- Add scheduled task startup detection.
- Add publisher/signature metadata where available.

## Repair

- Stream long command output into the UI.
- Add Windows Update repair group using supported mechanisms.
- Add restart-required dashboard state.
- Add event log summary.

## Expert Lab

- Implement registry export plus reversible writes for selected safe tweaks.
- Add more Explorer, taskbar, context menu, telemetry, and visual effect tweaks only when each can be previewed and rolled back.
- Keep risky/expert tweaks unselected by default.

## Packaging

- Add PyInstaller config.
- Generate signed release artifacts later if the business workflow requires it.
- Add app update strategy without cloud dependency for MVP.
