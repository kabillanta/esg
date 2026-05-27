from decimal import Decimal, InvalidOperation
from datetime import datetime
from .base import BaseParser
from ingestion.models import FacilityMapping

# ── Keyword → category mapping ──────────────────────────────────────
# SAP's TXZ01 (short text) is free-form.  We scan it for known
# German / English keywords and assign a canonical category.
_CATEGORY_KEYWORDS = [
    # (search tokens,                        category)
    (['diesel'],                             'diesel'),
    (['benzin'],                             'gasoline'),
    (['super benzin'],                       'gasoline'),
    (['super e10'],                          'gasoline'),
    (['gas', 'benzin'],                      'gasoline'),   # "Super Benzin", etc.
    (['bio diesel', 'biodiesel'],            'biodiesel'),
    (['heizöl', 'heizoel', 'heating oil'],   'heating_oil'),
    (['erdgas', 'cng', 'natural gas'],       'natural_gas'),
    (['flüssiggas', 'lpg', 'propane'],       'lpg'),
    (['kerosin', 'kerosene', 'jet fuel'],    'kerosene'),
    (['adblue', 'def'],                      'adblue'),
]


def _categorise_fuel(short_text: str) -> str:
    """Derive a fuel category from the SAP material short-text (TXZ01)."""
    text = short_text.lower()
    for keywords, category in _CATEGORY_KEYWORDS:
        if any(kw in text for kw in keywords):
            return category
    return 'unknown_fuel'


class SAPFuelParser(BaseParser):
    """
    Parses SAP flat-file exports for fuel / procurement data.

    Expected CSV columns (SAP technical names):
        WERKS  – Plant code
        MATNR  – Material number
        TXZ01  – Material short text (free-form, may be German)
        MENGE  – Quantity  (European format: 12.500,00)
        MEINS  – Unit of measure (SAP internal code, e.g. L, GAL, KG)
        NETPR  – Net price
        WAERS  – Currency
        BUDAT  – Posting date (YYYYMMDD)
        LIFNR  – Vendor number
        EKGRP  – Purchasing group
        BELNR  – Document number
    """

    def __init__(self, upload_batch):
        super().__init__(upload_batch)
        # Pre-load the facility mapping for this org so we can do
        # O(1) lookups per row instead of a query per row.
        self._facility_map = {
            fm.plant_code: fm
            for fm in FacilityMapping.objects.filter(
                organization=self.organization
            )
        }

    def get_scope(self):
        return 'SCOPE_1'

    def parse_row(self, row):
        # ── Quantity (European decimal) ──────────────────────────────
        menge_str = row.get('MENGE', '0').replace('.', '').replace(',', '.')
        try:
            quantity = Decimal(menge_str)
        except (InvalidOperation, ValueError):
            raise ValueError(f"Invalid quantity: {row.get('MENGE')}")

        if quantity < 0:
            raise ValueError(f"Negative quantity: {quantity}")

        # ── Date ─────────────────────────────────────────────────────
        budat = row.get('BUDAT', '').strip()
        try:
            activity_date = datetime.strptime(budat, '%Y%m%d').date()
        except (ValueError, TypeError):
            raise ValueError(f"Invalid date: {budat}")

        # ── Category ─────────────────────────────────────────────────
        short_text = row.get('TXZ01', '')
        category = _categorise_fuel(short_text)

        # ── Facility mapping ─────────────────────────────────────────
        werks = row.get('WERKS', '').strip()
        facility = self._facility_map.get(werks)
        facility_name = facility.facility_name if facility else ''

        result = {
            'activity_date': activity_date,
            'category': category,
            'description': short_text.strip(),
            'quantity_original': quantity,
            'unit_original': row.get('MEINS', 'L'),
            'facility_code': werks,
            'facility_name': facility_name,
            'vendor_or_provider': row.get('LIFNR', ''),
        }

        # If the plant code is unknown, we still ingest the row but
        # mark it as an anomaly so the analyst can map it later.
        if werks and not facility:
            result['_unmapped_werks'] = True

        return result
