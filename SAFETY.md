# Safety Model

Cingy.Tech ToolKit is designed as a professional service tool, not a hidden optimizer.

## Core Rules

- Every system-changing operation must be an `Action`.
- Every action has an ID, title, category, description, risk level, admin requirement, preview, execution result, and rollback information where possible.
- Dry-run preview comes before execution.
- Execution requires explicit confirmation.
- Admin-only actions check admin status before running.
- Risky and expert actions are never selected by default.
- Logs are written for action ID, title, safe command preview, result, stdout/stderr summary, and before/after values where available.

## Forbidden Actions

- Do not disable Microsoft Defender.
- Do not disable Windows Update completely.
- Do not apply unknown registry hacks.
- Do not delete system folders manually.
- Do not remove Microsoft Edge forcibly.
- Do not remove OneDrive without explicit selection and customer approval.
- Do not remove Microsoft Store framework dependencies blindly.
- Do not claim performance gains that were not measured.
- Do not use third-party driver updater logic.
- Do not perform activation, cracking, or KMS actions.
- Do not hide commands from the log.
- Do not delete personal files.
- Do not clean Downloads by default.
- Do not run PowerShell commands built from unsanitized user input.

## PowerShell Safety

PowerShell commands are run through `PowerShellRunner` with `shell=False`. The MVP uses fixed command strings from code or JSON rules, not raw user input.

The runner blocks known forbidden command fragments related to disabling security, disabling Windows Update, activation/KMS, and broad destructive deletes.

## Registry Safety

Expert registry tweaks are rule-backed and gated behind the Expert Lab warning. Each tweak must define:

- hive
- path
- value name
- value type
- target value
- rollback value
- description
- risk
- restart requirement
- source comment

The MVP previews registry values and creates backup metadata. It intentionally does not offer an apply-all expert flow.

## Cleanup Safety

The MVP only implements direct deletion for known temp paths and refuses paths outside approved temp roots. Recycle Bin, thumbnail cache, DirectX shader cache, Delivery Optimization, browser cache, and Downloads cleanup are preview or placeholder flows until dedicated safe mechanisms are implemented.

Downloads reporting is allowed. Downloads deletion is not a default action.
