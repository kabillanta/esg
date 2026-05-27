from decimal import Decimal

# ── SAP internal unit-of-measure codes ───────────────────────────────
# SAP uses two- or three-letter codes that may appear in MEINS.
# This mapping converts them to the lowercase canonical strings
# understood by the rest of the normalizer.
SAP_UNIT_MAP = {
    'L':   'l',
    'LTR': 'l',
    'GAL': 'gal',
    'TO':  'to',       # metric tonne
    'KG':  'kg',
    'G':   'g',
    'M3':  'm3',       # cubic metre
    'ST':  'st',       # Stück / piece  (not convertible – pass through)
    'KWH': 'kwh',
    'MWH': 'mwh',
}


def _resolve_sap_unit(raw_unit: str) -> str:
    """Map an SAP-internal unit code to a normalizer-friendly string."""
    cleaned = raw_unit.strip().upper()
    return SAP_UNIT_MAP.get(cleaned, raw_unit.strip().lower())


def normalize_quantity_and_unit(quantity, unit):
    """
    Normalizes a given quantity and unit to a canonical format.
    Returns (normalized_quantity, canonical_unit, category_hint).
    """
    unit = _resolve_sap_unit(str(unit))
    quantity = Decimal(str(quantity))

    # ── Volume (Fuel) → Liters ───────────────────────────────────────
    if unit in ('l', 'liters', 'liter', 'ltr'):
        return quantity, 'liters', None
    elif unit in ('gal', 'gallons', 'gallon'):
        return quantity * Decimal('3.78541'), 'liters', None
    elif unit == 'm3':
        # 1 m³ of liquid fuel ≈ 1 000 L  (acceptable for diesel/petrol)
        return quantity * Decimal('1000'), 'liters', None

    # ── Mass → kg ────────────────────────────────────────────────────
    elif unit in ('kg', 'kilogram', 'kilograms'):
        return quantity, 'kg', None
    elif unit in ('to', 'tonne', 'tonnes', 't'):
        return quantity * Decimal('1000'), 'kg', None
    elif unit in ('g', 'gram', 'grams'):
        return quantity / Decimal('1000'), 'kg', None

    # ── Energy → kWh ─────────────────────────────────────────────────
    elif unit in ('kwh',):
        return quantity, 'kWh', 'electricity_us'
    elif unit in ('mwh',):
        return quantity * Decimal('1000'), 'kWh', 'electricity_us'
    elif unit in ('therms', 'therm'):
        return quantity * Decimal('29.3001'), 'kWh', 'natural_gas'

    # ── Distance → km ────────────────────────────────────────────────
    elif unit in ('km', 'kilometers', 'kilometer'):
        return quantity, 'km', None
    elif unit in ('mi', 'miles', 'mile'):
        return quantity * Decimal('1.60934'), 'km', None

    # ── Count-based (hotel nights, pieces) ───────────────────────────
    elif unit in ('night', 'nights'):
        return quantity, 'night', 'hotel_night'
    elif unit in ('st', 'piece', 'pieces', 'ea'):
        return quantity, 'piece', None

    # ── Default fallback ─────────────────────────────────────────────
    return quantity, unit, None
