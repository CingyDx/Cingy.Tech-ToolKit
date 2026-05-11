from pathlib import Path

import pytest

from app.core.powershell_runner import PowerShellRunner
from app.core.safety import SafetyViolation, assert_safe_powershell_script
from app.core.state_store import JsonRuleStore


def test_rule_store_validates_required_fields(tmp_path):
    rule_file = tmp_path / "rules.json"
    rule_file.write_text('[{"id": "safe.cleanup", "title": "Safe cleanup"}]', encoding="utf-8")

    store = JsonRuleStore(tmp_path)

    errors = store.validate_rule_file("rules.json", required_fields={"id", "title", "risk"})

    assert errors
    assert "risk" in errors[0]


def test_rule_store_loads_valid_rules_from_repo():
    root = Path(__file__).resolve().parents[1]
    store = JsonRuleStore(root / "app" / "rules")

    presets = store.load_required("presets.json")
    install_packs = store.load_required("install_packs.json")

    assert any(preset["id"] == "safe_cleanup" for preset in presets["presets"])
    assert any(pack["id"] == "basic_pack" for pack in install_packs["packs"])


def test_safety_violation_is_specific_exception_type():
    error = SafetyViolation("unsafe command")

    assert isinstance(error, RuntimeError)


def test_powershell_safety_blocks_command_separators():
    with pytest.raises(SafetyViolation):
        assert_safe_powershell_script("ipconfig /flushdns; ipconfig /displaydns")


def test_powershell_preview_shows_safe_command_text():
    preview = PowerShellRunner(executable="powershell.exe").preview("ipconfig /flushdns")

    assert "ipconfig /flushdns" in preview
