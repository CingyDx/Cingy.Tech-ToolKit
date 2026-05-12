from app.core.score import calculate_health_score
from app.core.recommendations import recommendations_from_snapshot
from app.core.scanner import (
    extract_gpu_names,
    estimate_directory_size,
    parse_activation_status,
    parse_windows_update_status,
    summarize_system_snapshot,
)


def test_health_score_is_transparent_and_penalizes_known_risks():
    snapshot = {
        "system_drive_used_percent": 94,
        "startup_item_count": 24,
        "detected_bloatware_count": 9,
        "ram_used_percent": 88,
        "repair_warning_count": 2,
        "temp_cache_estimated_bytes": 7 * 1024 * 1024 * 1024,
    }

    result = calculate_health_score(snapshot)

    assert result.score < 70
    assert any("disk" in item.lower() for item in result.explanations)
    assert any("startup" in item.lower() for item in result.explanations)


def test_estimate_directory_size_returns_zero_for_missing_path(tmp_path):
    missing = tmp_path / "does-not-exist"

    assert estimate_directory_size(missing) == 0


def test_system_snapshot_summary_contains_customer_safe_fields():
    summary = summarize_system_snapshot(
        {
            "device_name": "DESKTOP-TEST",
            "windows_version": "Windows 11 Pro build 22631",
            "cpu": "Example CPU",
            "ram_total_gb": 16,
            "gpu": "Unknown",
            "admin_status": False,
            "health_score": 82,
        }
    )

    assert summary["device_name"] == "DESKTOP-TEST"
    assert summary["admin_status"] is False
    assert "health_score" in summary


def test_parse_activation_status_from_cim_output():
    output = "LicenseStatus : 1\nName : Windows(R), Professional edition"

    assert parse_activation_status(output) == "Windows je aktivovaný"


def test_extract_gpu_names_ignores_class_name_fields():
    output = "Name : NVIDIA GeForce RTX\nCreationClassName : Win32_VideoController"

    assert extract_gpu_names(output) == "NVIDIA GeForce RTX"


def test_parse_windows_update_status_from_cim_output():
    output = "LastSearchSuccessDate : 2026-05-10 12:30:00"

    assert parse_windows_update_status(output) == "Poslední kontrola aktualizací: 2026-05-10 12:30:00"


def test_parse_windows_update_status_from_get_hotfix_table():
    output = """
Source        Description      HotFixID      InstalledBy          InstalledOn
------        -----------      --------      -----------          -----------
PC            Update           KB1           SYSTEM               4/18/2026 12:00:00 AM
PC            Security Update  KB2           SYSTEM               4/19/2026 12:00:00 AM
"""

    assert parse_windows_update_status(output) == "Poslední nalezený hotfix: 4/19/2026 12:00:00 AM"


def test_recommendations_from_snapshot_are_plain_and_specific():
    recommendations = recommendations_from_snapshot(
        {
            "system_drive_used_percent": 92,
            "ram_total_gb": 4,
            "startup_item_count": 18,
            "boot_drive_type": "HDD",
            "temp_cache_estimated_bytes": 6 * 1024 * 1024 * 1024,
        }
    )

    assert "Disk C má málo volného místa" in recommendations[0]
    assert any("SSD" in item for item in recommendations)
    assert all("10x" not in item for item in recommendations)
