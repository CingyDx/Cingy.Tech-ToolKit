from app.core.score import calculate_health_score
from app.core.scanner import estimate_directory_size, summarize_system_snapshot


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
