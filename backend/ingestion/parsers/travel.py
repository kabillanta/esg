"""
Corporate-travel expense parser (Concur / Navan CSV export format).

Handles three travel sub-categories:
  • Flights  – uses IATA airport-code lookup + Haversine distance when
               the Distance (miles) field is empty.
  • Hotels   – quantity = Number of Nights.
  • Ground   – taxis, car rentals, rideshares.
"""
from decimal import Decimal, InvalidOperation
from datetime import datetime
from .base import BaseParser
from ingestion.airport_lookup import lookup_distance_km, classify_flight_haul


class TravelParser(BaseParser):
    """
    Expected CSV columns (Concur-style):
        Report ID, Employee Name, Expense Type, Transaction Date,
        Amount, Currency, Origin, Destination, Hotel City,
        Number of Nights, Distance (miles), Travel Class
    """

    def get_scope(self):
        return 'SCOPE_3'

    def parse_row(self, row):
        expense_type = str(row.get('Expense Type', '')).lower()

        # ── Date ─────────────────────────────────────────────────────
        tx_date = row.get('Transaction Date', '').strip()
        try:
            activity_date = datetime.strptime(tx_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            raise ValueError(f"Invalid date: {tx_date}")

        # ── Flights ──────────────────────────────────────────────────
        if 'flight' in expense_type or 'airfare' in expense_type:
            return self._parse_flight(row, activity_date)

        # ── Hotels ───────────────────────────────────────────────────
        if 'hotel' in expense_type:
            return self._parse_hotel(row, activity_date)

        # ── Ground transport ─────────────────────────────────────────
        if any(kw in expense_type for kw in ('car', 'taxi', 'transport', 'rideshare', 'uber', 'lyft')):
            return self._parse_ground(row, activity_date, expense_type)

        raise ValueError(f"Unknown expense type: {expense_type}")

    # ── Flight ───────────────────────────────────────────────────────
    def _parse_flight(self, row, activity_date):
        origin = (row.get('Origin', '') or '').strip().upper()
        dest   = (row.get('Destination', '') or '').strip().upper()
        travel_class = row.get('Travel Class', 'Economy')

        # Try the Distance column first; fall back to airport lookup
        raw_dist = str(row.get('Distance (miles)', '') or '').strip()
        distance_km = None

        if raw_dist:
            try:
                distance_miles = Decimal(raw_dist)
                distance_km = distance_miles * Decimal('1.60934')
            except (InvalidOperation, ValueError):
                distance_km = None

        if distance_km is None and origin and dest:
            looked_up = lookup_distance_km(origin, dest)
            if looked_up is not None:
                distance_km = Decimal(str(looked_up))

        category = classify_flight_haul(distance_km)

        return {
            'activity_date': activity_date,
            'category': category,
            'description': (
                f"Flight: {origin or '???'} → {dest or '???'} "
                f"({travel_class})"
            ),
            'quantity_original': distance_km if distance_km is not None else Decimal('0'),
            'unit_original': 'km',
            'vendor_or_provider': 'Airlines',
        }

    # ── Hotel ────────────────────────────────────────────────────────
    def _parse_hotel(self, row, activity_date):
        nights_str = str(row.get('Number of Nights', '') or '').strip()
        nights = Decimal(nights_str) if nights_str else Decimal('1')
        city = row.get('Hotel City', '') or ''

        return {
            'activity_date': activity_date,
            'category': 'hotel_night',
            'description': f"Hotel stay in {city}" if city else 'Hotel stay (city unknown)',
            'quantity_original': nights,
            'unit_original': 'night',
        }

    # ── Ground transport ─────────────────────────────────────────────
    def _parse_ground(self, row, activity_date, expense_type):
        category = 'taxi' if 'taxi' in expense_type else 'rental_car'

        raw_dist = str(row.get('Distance (miles)', '') or '').strip()
        if raw_dist:
            try:
                distance_km = Decimal(raw_dist) * Decimal('1.60934')
            except (InvalidOperation, ValueError):
                distance_km = Decimal('0')
        else:
            distance_km = Decimal('0')

        return {
            'activity_date': activity_date,
            'category': category,
            'description': f"Ground transport – {expense_type}",
            'quantity_original': distance_km,
            'unit_original': 'km',
        }
