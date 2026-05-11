# TODO

## UX / Design

- [ ] Add real visual QA screenshots to the repository documentation after the UI stabilizes.
- [ ] Add icons or polished vector marks for each mode card.
- [ ] Add persisted last-scan state shared between Home, Scan, and Reports.
- [ ] Add live progress updates for long-running repair actions.
- [ ] Add richer Czech/English translation handling if English UI becomes a real requirement.

## Implementation

- [ ] Confirm all winget package IDs in `app/rules/install_packs.json` before enabling install execution.
- [ ] Add real AppX package scan to Debloat page.
- [ ] Add safe Recycle Bin empty executor with final confirmation.
- [ ] Add Windows Update status read-only check.
- [ ] Add Windows activation read-only check.
- [ ] Add disk type and health detection.
- [ ] Add startup disable/enable with backup.
- [ ] Add registry tweak write/undo implementation for safe Expert Lab entries.
- [ ] Add streaming command output for SFC/DISM.
- [ ] Add before/after snapshot capture around executed plans.
- [ ] Add report recommendations from scanner facts.
