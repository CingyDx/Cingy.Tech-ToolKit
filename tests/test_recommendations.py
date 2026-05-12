from app.core.recommendations import recommendations_from_snapshot


def test_recommendations_return_ok_message_for_clean_snapshot():
    recommendations = recommendations_from_snapshot(
        {
            "system_drive_used_percent": 40,
            "ram_total_gb": 16,
            "startup_item_count": 3,
            "boot_drive_type": "SSD",
            "temp_cache_estimated_bytes": 100 * 1024 * 1024,
        }
    )

    assert recommendations == ["Nebyla nalezena žádná zásadní servisní doporučení."]
