from app.modules.debloat.manager import BloatwareManager


def test_debloat_matches_appx_inventory_against_rules(tmp_path):
    manager = BloatwareManager()
    rules = [
        {
            "id": "consumer.example",
            "display_name": "Consumer Example",
            "match_patterns": ["Microsoft.ExampleApp"],
            "type": "appx",
            "risk": "safe",
            "reason": "Consumer app",
            "uninstall_method": "appx_remove_package",
            "can_remove": True,
        }
    ]

    detected = manager.match_inventory(
        rules,
        desktop_apps=[],
        appx_packages=[{"name": "Microsoft.ExampleApp", "publisher": "Microsoft"}],
    )

    assert len(detected) == 1
    assert detected[0].app_type == "appx"
    assert detected[0].name == "Microsoft.ExampleApp"
