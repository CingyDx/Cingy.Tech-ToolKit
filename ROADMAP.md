# Roadmap

## Next Pass

- Add SMART/disk health where safely available.
- Improve Windows Update status with official Windows Update API details if a safe non-blocking wrapper is added.
- Add browser cache cleanup with explicit browser selection and warnings.
- Add before/after snapshot capture around action execution.
- Persist last scan state across Home, Scan, and Reports instead of generating a fresh report scan.

## Debloat

- Add final confirmation and supported uninstall execution for selected safe AppX/desktop apps.
- Add final confirmation summary for selected removals.
- Add undo/backup notes for each supported uninstall method.
- Keep OneDrive and Microsoft framework packages protected unless explicitly selected with clear warnings.

## Startup Manager

- Add scheduled task startup detection.
- Add publisher/signature metadata where available.

## Repair

- Stream long command output into the UI.
- Add Windows Update repair group using supported mechanisms.
- Add restart-required dashboard state.
- Add event log summary.

## Expert Lab

- Add more Explorer, taskbar, context menu, telemetry, and visual effect tweaks only when each can be previewed and rolled back.
- Keep risky/expert tweaks unselected by default.

## Packaging

- Add PyInstaller config.
- Generate signed release artifacts later if the business workflow requires it.
- Add app update strategy without cloud dependency for MVP.
