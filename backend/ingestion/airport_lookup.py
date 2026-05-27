"""
Airport coordinate lookup and great-circle distance calculator.

Contains a curated subset of major IATA airports sufficient for the
demo dataset.  In production this would be backed by the OpenFlights
database (~7 000 rows) loaded into a DB table or an in-memory CSV.
"""
import math
from decimal import Decimal

# ── IATA → (latitude, longitude) ─────────────────────────────────────
# Source: https://openflights.org/data.html  (rounded to 4 dp)
AIRPORT_COORDS = {
    # North America
    'SFO': (37.6213, -122.3790),
    'JFK': (40.6413, -73.7781),
    'LAX': (33.9425, -118.4081),
    'ORD': (41.9742, -87.9073),
    'BOS': (42.3656, -71.0096),
    'SEA': (47.4502, -122.3088),
    'ATL': (33.6407, -84.4277),
    'DFW': (32.8998, -97.0403),
    'MIA': (25.7959, -80.2870),
    'IAD': (38.9531, -77.4565),
    'EWR': (40.6895, -74.1745),
    'DEN': (39.8561, -104.6737),

    # Europe
    'LHR': (51.4700, -0.4543),
    'CDG': (49.0097, 2.5479),
    'FRA': (50.0379, 8.5622),
    'AMS': (52.3105, 4.7683),
    'MAD': (40.4983, -3.5676),
    'FCO': (41.8003, 12.2389),
    'MXP': (45.6306, 8.7281),
    'MUC': (48.3537, 11.7750),
    'ZRH': (47.4647, 8.5492),

    # Middle East
    'DXB': (25.2532, 55.3657),
    'DOH': (25.2731, 51.6081),

    # Asia
    'BOM': (19.0896, 72.8656),
    'DEL': (28.5562, 77.1000),
    'SIN': (1.3644, 103.9915),
    'HND': (35.5533, 139.7811),
    'NRT': (35.7720, 140.3929),
    'ICN': (37.4602, 126.4407),
    'HKG': (22.3080, 113.9185),
    'PEK': (40.0799, 116.6031),

    # Oceania
    'SYD': (-33.9461, 151.1772),

    # South America
    'GRU': (-23.4356, -46.4731),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in **kilometres** between two points."""
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def lookup_distance_km(origin_iata: str, dest_iata: str):
    """
    Return the great-circle distance in km between two IATA airport codes.
    Returns ``None`` if either code is not found in the lookup table.
    """
    origin_iata = (origin_iata or '').strip().upper()
    dest_iata = (dest_iata or '').strip().upper()
    if origin_iata not in AIRPORT_COORDS or dest_iata not in AIRPORT_COORDS:
        return None
    lat1, lon1 = AIRPORT_COORDS[origin_iata]
    lat2, lon2 = AIRPORT_COORDS[dest_iata]
    return round(_haversine_km(lat1, lon1, lat2, lon2), 2)


# ── Flight-distance buckets (DEFRA thresholds) ──────────────────────
SHORT_HAUL_MAX_KM = 483       # ~300 miles
MEDIUM_HAUL_MAX_KM = 3700     # ~2 300 miles


def classify_flight_haul(distance_km) -> str:
    """
    Return a category string based on the great-circle distance.
    Uses DEFRA-style thresholds.
    """
    if distance_km is None:
        return 'flight_unknown_haul'
    d = float(distance_km)
    if d <= SHORT_HAUL_MAX_KM:
        return 'flight_short_haul'
    elif d <= MEDIUM_HAUL_MAX_KM:
        return 'flight_medium_haul'
    return 'flight_long_haul'
