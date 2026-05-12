from __future__ import annotations

from typing import Any


def recommendations_from_snapshot(snapshot: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    used_percent = int(snapshot.get("system_drive_used_percent") or 0)
    ram_gb = float(snapshot.get("ram_total_gb") or 0)
    startup_count = int(snapshot.get("startup_item_count") or 0)
    temp_bytes = int(snapshot.get("temp_cache_estimated_bytes") or 0)
    boot_drive_type = str(snapshot.get("boot_drive_type") or "unknown").upper()
    update_status = str(snapshot.get("windows_update_status") or "")

    if used_percent >= 90:
        recommendations.append("Disk C má málo volného místa. Doporučeno uvolnit místo nebo zvětšit disk.")
    elif used_percent >= 85:
        recommendations.append("Disk C je hodně zaplněný. Doporučeno zkontrolovat velké soubory a dočasná data.")

    if 0 < ram_gb < 8:
        recommendations.append("RAM je pro Windows slabší. Doporučeno zvážit upgrade alespoň na 8 GB.")

    if boot_drive_type == "HDD":
        recommendations.append("Disk je HDD, doporučena výměna za SSD pro běžnou odezvu systému.")

    if startup_count >= 15:
        recommendations.append("Po startu se spouští hodně aplikací. Doporučeno ručně vypnout nepotřebné položky.")

    if temp_bytes >= 5 * 1024**3:
        recommendations.append("Dočasné/cache soubory zabírají více než 5 GB. Doporučeno bezpečné vyčištění.")

    if "nepodařilo" in update_status.lower() or "unknown" in update_status.lower():
        recommendations.append("Stav Windows Update není jistý. Doporučeno ručně ověřit aktualizace ve Windows Nastavení.")

    if not recommendations:
        return ["Nebyla nalezena žádná zásadní servisní doporučení."]
    return recommendations
