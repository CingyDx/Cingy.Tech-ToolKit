from app.config import AppConfig


def test_config_defaults_to_czech_and_hides_advanced_tools():
    config = AppConfig()

    assert config.language == "cs"
    assert config.show_advanced_tools is False
    assert config.enable_expert_lab is False
