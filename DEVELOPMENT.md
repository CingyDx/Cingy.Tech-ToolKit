# Development Notes

## Architecture

The toolkit is organized around a central action engine.

```text
app/
  core/       action model, engine, scanner, score, runners, reports
  modules/    domain modules that create Action objects
  rules/      JSON rule metadata for presets and future modules
  ui/         PySide6 pages and worker threads
```

UI callbacks should not hardcode dangerous system commands. Pages should ask modules for actions, preview through `ActionEngine.preview_plan()`, and execute through `ActionEngine.execute_plan()`.

The default UX is organized around `app/core/modes.py` and `app/rules/modes.json`. Home and Modes use this customer-facing layer to build safe action plans from existing `Action` objects. Advanced pages remain available behind technician mode, but they should not become the default customer workflow.

## Action Lifecycle

1. Build an `Action`.
2. Preview it in dry-run mode.
3. Show the plan to the technician.
4. Require explicit confirmation.
5. Check admin and risk gates.
6. Execute in a worker thread for long-running work.
7. Log the result.
8. Include the action in the report.

## Long Operations

Long-running actions such as SFC, DISM, cleanup, or repair commands should run through `QThread` workers. The GUI should remain responsive and show captured output or status.

## JSON Rules

Rules live in `app/rules/`. `JsonRuleStore.validate_startup_rules()` validates required fields and returns errors instead of crashing the app. Invalid rules should be logged and skipped in future passes.

## Testing

Current tests cover:

- action preview/execution gating
- confirmation and admin enforcement
- risky/expert default selection behavior
- transparent health scoring
- directory size estimation
- JSON rule validation
- mode catalog and mode action planning
- settings defaults for Czech and hidden advanced tools

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Packaging

Packaging is intentionally a later pass. The target shape is a portable executable plus local `logs/`, `reports/`, and `backups/` folders.
