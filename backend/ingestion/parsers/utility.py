"""
Utility electricity CSV parser with billing-period proration.

Splits a single utility bill that spans two (or more) calendar months
into multiple ``ActivityRecord`` rows, each attributed to the correct
month.  This avoids the classic problem of utility bills that run from
mid-Jan to mid-Feb being dumped entirely into one month.
"""
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timedelta
from .base import BaseParser


def _month_boundary_split(start: date, end: date, total_quantity: Decimal):
    """
    Yield ``(month_date, prorated_quantity)`` tuples by splitting the
    total evenly across the calendar days in each month the billing
    period spans.

    ``month_date`` is the first day of each affected month (used as the
    ``activity_date`` for the resulting record).
    """
    total_days = (end - start).days
    if total_days <= 0:
        # Degenerate – single-day or invalid range
        yield start.replace(day=1), total_quantity
        return

    daily_rate = total_quantity / Decimal(str(total_days))

    cursor = start
    while cursor < end:
        # End of the current month (or the billing-end, whichever is first)
        month_end = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)  # 1st of next month
        segment_end = min(month_end, end)
        days_in_segment = (segment_end - cursor).days
        prorated_qty = (daily_rate * Decimal(str(days_in_segment))).quantize(Decimal('0.0001'))

        yield cursor.replace(day=1), prorated_qty
        cursor = segment_end


class UtilityParser(BaseParser):
    """
    Parses utility-portal CSV exports for electricity consumption.

    Expected columns:
        Account Number, Meter ID, Service Address,
        Billing Start Date, Billing End Date,
        Total kWh, Peak Demand kW, Read Type,
        Total Charges ($), Rate Schedule
    """

    def get_scope(self):
        return 'SCOPE_2'

    # ── Override process_file to handle proration ────────────────────
    # The base class calls ``parse_row`` once per CSV row and creates
    # one ``ActivityRecord``.  For utility data we may need to emit
    # *multiple* records from a single row (one per calendar month).
    # We override ``parse_row`` to return a list.

    def parse_row(self, row):
        """
        Returns a **list** of parsed-data dicts (one per prorated month).
        The base class ``process_file`` is patched to handle this.
        """
        # ── Quantity ─────────────────────────────────────────────────
        kwh_str = str(row.get('Total kWh', '0')).replace(',', '')
        try:
            quantity = Decimal(kwh_str)
        except (InvalidOperation, ValueError):
            raise ValueError(f"Invalid quantity: {row.get('Total kWh')}")

        # ── Dates ────────────────────────────────────────────────────
        start_str = row.get('Billing Start Date', '').strip()
        end_str   = row.get('Billing End Date', '').strip()
        try:
            billing_start = datetime.strptime(start_str, '%m/%d/%Y').date()
        except (ValueError, TypeError):
            raise ValueError(f"Invalid billing start date: {start_str}")
        try:
            billing_end = datetime.strptime(end_str, '%m/%d/%Y').date()
        except (ValueError, TypeError):
            raise ValueError(f"Invalid billing end date: {end_str}")

        if billing_end <= billing_start:
            raise ValueError(
                f"Billing end date ({end_str}) must be after start date ({start_str})"
            )

        # ── Build one record per calendar-month slice ────────────────
        records = []
        for month_date, prorated_qty in _month_boundary_split(billing_start, billing_end, quantity):
            records.append({
                'activity_date': month_date,
                'category': 'electricity_us',
                'description': (
                    f"Billing: {start_str} to {end_str} "
                    f"(prorated to {month_date.strftime('%Y-%m')})"
                ),
                'quantity_original': prorated_qty,
                'unit_original': 'kWh',
                'facility_code': row.get('Meter ID', ''),
                'facility_name': row.get('Service Address', ''),
            })

        return records
