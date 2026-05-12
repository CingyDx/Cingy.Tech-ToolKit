# Safe Real Functionality Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace safe MVP placeholders with real read-only checks, reversible safe actions, and better report output.

**Architecture:** Keep the existing ActionEngine as the single execution path. Add focused helpers for Windows status, cleanup targets, registry-backed toggles, and report recommendations.

**Tech Stack:** Python 3.11, PySide6, psutil, winreg, PowerShellRunner, Jinja2, pytest.

---

### Task 1: Scanner Status And Recommendations

**Files:**
- Modify: `app/core/scanner.py`
- Create: `app/core/recommendations.py`
- Test: `tests/test_scanner.py`
- Test: `tests/test_recommendations.py`

- [ ] Add tests for activation/update status parsers and recommendation generation.
- [ ] Implement safe read-only scanner helpers with graceful `Unknown` fallback.
- [ ] Add report recommendations from disk, RAM, startup, temp, and update facts.
- [ ] Run targeted scanner/recommendation tests.

### Task 2: Safe Cleanup Executors

**Files:**
- Modify: `app/modules/cleanup/actions.py`
- Test: `tests/test_cleanup_actions.py`

- [ ] Add tests proving cleanup targets stay inside approved cache/temp roots.
- [ ] Implement Recycle Bin, thumbnail cache, DirectX shader cache, Delivery Optimization preview/execution with conservative paths and no Downloads deletion.
- [ ] Keep browser cleanup out of scope unless explicit browser selection exists.
- [ ] Run targeted cleanup tests.

### Task 3: Debloat And AppX Read-Only Detection

**Files:**
- Modify: `app/modules/debloat/manager.py`
- Modify: `app/ui/debloat_page.py`
- Test: `tests/test_debloat_manager.py`

- [ ] Add tests for matching desktop and AppX inventory against rules.
- [ ] Implement AppX package inventory using fixed PowerShell read-only command.
- [ ] Update UI copy to make removal/manual state clear.
- [ ] Run targeted debloat tests.

### Task 4: Registry-Backed Safe Toggles

**Files:**
- Modify: `app/core/registry_runner.py`
- Modify: `app/modules/privacy/toggles.py`
- Modify: `app/modules/expert_lab/registry_tweaks.py`
- Modify: `app/ui/privacy_page.py`
- Test: `tests/test_registry_actions.py`

- [ ] Add tests for safe registry action preview/write/undo metadata.
- [ ] Implement HKCU safe registry writes with JSON backup and undo actions.
- [ ] Keep risky/expert actions unselected by default.
- [ ] Run targeted registry tests.

### Task 5: Reports And Docs

**Files:**
- Modify: `app/ui/reports_page.py`
- Modify: `app/core/report_generator.py`
- Modify: `README.md`
- Modify: `TODO.md`
- Modify: `ROADMAP.md`
- Test: `tests/test_report_generator.py`

- [ ] Add tests for recommendations and report HTML content.
- [ ] Include latest scan/snapshot facts where available.
- [ ] Update docs to reflect implemented features and remaining packaging/admin work.
- [ ] Run full verification and security review.
