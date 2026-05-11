import pytest

from app.modules.startup.manager import (
    _assert_startup_entry_is_safe_to_disable,
    _decode_hkcu_run_id,
    _hkcu_run_id,
)


def test_hkcu_startup_entry_id_round_trips_names_with_spaces():
    entry_id = _hkcu_run_id("My Startup App")

    assert _decode_hkcu_run_id(entry_id) == "My Startup App"


def test_startup_disable_guard_blocks_security_items():
    with pytest.raises(ValueError):
        _assert_startup_entry_is_safe_to_disable("Windows Security", "SecurityHealthSystray.exe")
