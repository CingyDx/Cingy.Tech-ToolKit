from app.core.report_generator import ReportGenerator


def test_report_generator_includes_recommendations(tmp_path):
    report = ReportGenerator(output_dir=tmp_path).generate(
        system_info={"device_name": "DESKTOP-TEST"},
        recommendations=["Disk je HDD, doporučena výměna za SSD."],
    )

    html = report.read_text(encoding="utf-8")

    assert "DESKTOP-TEST" in html
    assert "Disk je HDD" in html
