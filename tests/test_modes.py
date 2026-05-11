from app.core.modes import ModeCatalog, build_mode_plan, friendly_action_title


def test_mode_catalog_has_customer_first_modes():
    catalog = ModeCatalog.load_default()

    visible_ids = [mode.id for mode in catalog.visible_modes()]

    assert visible_ids[:6] == [
        "safe_cleanup",
        "speed_up",
        "gaming",
        "school_work",
        "repair_windows",
        "custom",
    ]
    assert catalog.get("expert").technician_only is True
    assert catalog.get("expert").visible_by_default is False


def test_safe_cleanup_plan_uses_existing_safe_actions():
    catalog = ModeCatalog.load_default()

    plan = build_mode_plan(catalog.get("safe_cleanup"), is_admin=False)

    assert plan.mode_id == "safe_cleanup"
    assert plan.total_actions >= 2
    assert plan.risky_count == 0
    assert any(action.id == "cleanup.user_temp" for action in plan.actions)
    assert all(not action.is_risky_or_expert for action in plan.default_selected_actions)


def test_gaming_mode_does_not_auto_select_cleanup():
    catalog = ModeCatalog.load_default()

    plan = build_mode_plan(catalog.get("gaming"), is_admin=False)

    assert any(action.id == "cleanup.user_temp" for action in plan.actions)
    assert "cleanup.user_temp" not in {action.id for action in plan.default_selected_actions}


def test_repair_mode_summary_counts_admin_and_risky_actions():
    catalog = ModeCatalog.load_default()

    plan = build_mode_plan(catalog.get("repair_windows"), is_admin=False)

    assert plan.requires_admin_count > 0
    assert plan.advanced_count == 0
    assert plan.total_actions >= 4


def test_friendly_action_titles_hide_raw_command_names_by_default():
    assert friendly_action_title("repair.dism_restorehealth") == "Oprava obrazu Windows"
    assert friendly_action_title("repair.sfc_scan") == "Oprava systémových souborů"
