from decimal import Decimal
from datetime import date


def detect_anomaly(row_data, normalized_data, source_type):
    """
    Rule-based anomaly detection applied to every ingested row.
    Returns (is_anomaly: bool, anomaly_reason: str).
    """
    reasons = []

    # ── 1. Missing distances for transport ───────────────────────────
    if source_type in ('TRAVEL_GROUND', 'TRAVEL_FLIGHT'):
        qty = normalized_data.get('quantity_normalized')
        if not qty or qty <= 0:
            reasons.append("Missing or zero distance for travel record")

    # ── 2. Estimated meter reads for utility bills ───────────────────
    if source_type == 'UTILITY_ELECTRICITY':
        read_type = str(row_data.get('Read Type', '')).lower()
        if 'est' in read_type:
            reasons.append("Estimated meter reading used instead of actual")

    # ── 3. Unknown fuel category from SAP ────────────────────────────
    if source_type in ('SAP_FUEL', 'SAP_PROCUREMENT'):
        category = normalized_data.get('category', '')
        if category == 'unknown_fuel':
            reasons.append(
                f"Could not classify fuel from material text: "
                f"{row_data.get('TXZ01', '(empty)')}"
            )

    # ── 4. Unknown flight haul (no distance, no airport match) ───────
    if source_type == 'TRAVEL_FLIGHT':
        category = normalized_data.get('category', '')
        if category == 'flight_unknown_haul':
            reasons.append(
                "Could not determine flight distance – "
                "no distance provided and airport codes not found in lookup"
            )

    # ── 5. Hard quantity limit (> 1 000 000 of any unit) ─────────────
    qty = normalized_data.get('quantity_normalized')
    if qty and qty > Decimal('1000000'):
        reasons.append(
            f"Unusually high quantity: {qty} "
            f"{normalized_data.get('unit_normalized')}"
        )

    # ── 6. Future dates ──────────────────────────────────────────────
    activity_date = normalized_data.get('activity_date')
    if activity_date and isinstance(activity_date, date) and activity_date > date.today():
        reasons.append(f"Activity date is in the future: {activity_date}")

    if reasons:
        return True, "; ".join(reasons)

    return False, ""
