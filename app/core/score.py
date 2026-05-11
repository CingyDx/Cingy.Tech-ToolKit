from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class HealthScore:
    score: int
    explanations: list[str] = field(default_factory=list)
    factors: dict[str, int] = field(default_factory=dict)


def _penalize(factors: dict[str, int], explanations: list[str], name: str, points: int, text: str) -> None:
    if points <= 0:
        return
    factors[name] = -points
    explanations.append(text)


def calculate_health_score(snapshot: dict[str, object]) -> HealthScore:
    score = 100
    explanations: list[str] = []
    factors: dict[str, int] = {}

    disk_used = int(snapshot.get("system_drive_used_percent") or 0)
    if disk_used >= 92:
        penalty = 22
        text = f"System drive disk usage is very high ({disk_used}%)."
    elif disk_used >= 85:
        penalty = 15
        text = f"System drive disk usage is high ({disk_used}%)."
    elif disk_used >= 75:
        penalty = 8
        text = f"System drive disk usage is getting high ({disk_used}%)."
    else:
        penalty = 0
        text = ""
    _penalize(factors, explanations, "system_drive_fullness", penalty, text)

    startup_count = int(snapshot.get("startup_item_count") or 0)
    if startup_count >= 20:
        _penalize(factors, explanations, "startup_items", 12, f"Startup item count is high ({startup_count}).")
    elif startup_count >= 10:
        _penalize(factors, explanations, "startup_items", 6, f"Startup item count is moderate ({startup_count}).")

    bloatware_count = int(snapshot.get("detected_bloatware_count") or 0)
    if bloatware_count >= 10:
        _penalize(factors, explanations, "bloatware", 10, f"Detected bloatware count is high ({bloatware_count}).")
    elif bloatware_count >= 5:
        _penalize(factors, explanations, "bloatware", 6, f"Detected bloatware count is moderate ({bloatware_count}).")

    ram_used = int(snapshot.get("ram_used_percent") or 0)
    if ram_used >= 90:
        _penalize(factors, explanations, "ram_pressure", 10, f"RAM pressure is high ({ram_used}% used).")
    elif ram_used >= 80:
        _penalize(factors, explanations, "ram_pressure", 5, f"RAM pressure is elevated ({ram_used}% used).")

    warnings = int(snapshot.get("repair_warning_count") or 0)
    if warnings:
        _penalize(factors, explanations, "repair_warnings", min(15, warnings * 5), f"Repair warnings detected ({warnings}).")

    temp_bytes = int(snapshot.get("temp_cache_estimated_bytes") or 0)
    gib = temp_bytes / (1024**3)
    if gib >= 5:
        _penalize(factors, explanations, "temp_cache", 6, f"Temporary/cache files are sizable ({gib:.1f} GB).")
    elif gib >= 2:
        _penalize(factors, explanations, "temp_cache", 3, f"Temporary/cache files are noticeable ({gib:.1f} GB).")

    score += sum(factors.values())
    score = max(0, min(100, score))
    if not explanations:
        explanations.append("No major scoring warnings were detected by the transparent MVP checks.")
    return HealthScore(score=score, explanations=explanations, factors=factors)
