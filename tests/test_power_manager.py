from app.modules.power.manager import parse_power_plans


def test_parse_powercfg_list_keeps_real_plan_names_and_active_state():
    output = """
Existing Power Schemes (* Active)
-----------------------------------
Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced)
Power Scheme GUID: 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  (High performance)
Power Scheme GUID: 09b0c066-4da3-4919-9aef-08e1a5819ef6  (Ultimate Performance) *
"""

    plans = parse_power_plans(output)

    assert [plan.name for plan in plans] == ["Balanced", "High performance", "Ultimate Performance"]
    assert plans[2].is_active is True
    assert plans[0].guid == "381b4222-f694-41f0-9685-ff5bb260df2e"
