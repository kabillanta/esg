# Data Model Architecture

The data architecture for Breathe ESG is designed around three pillars: **auditable data lineage**, **multi-tenant isolation**, and **separation of raw, normalized, and computed values**.

---

## Entity-Relationship Overview

```
Organization (tenant root)
 ├── User (ADMIN | ANALYST)
 ├── DataSource (SAP_FUEL | SAP_PROCUREMENT | UTILITY_ELECTRICITY | TRAVEL_*)
 │    └── UploadBatch (per file ingestion)
 │         └── ActivityRecord* (one per source row, or multiple via proration)
 ├── FacilityMapping (WERKS plant code → human-readable name)
 └── EmissionFactor (category + unit → kg CO₂e conversion)
```

---

## Core Models

### 1. `ActivityRecord` — The Source of Truth

The central entity. Every record captures:

| Layer | Fields | Purpose |
|-------|--------|---------|
| **Raw lineage** | `raw_data` (JSON), `source_row_number`, `upload_batch` | Exact reproduction of the original CSV row. If an auditor questions a number, we can trace it to the original file, row, and batch. |
| **Original values** | `quantity_original`, `unit_original` | The user's input as-is (e.g., `12.500,00 L` for SAP, `45,230 kWh` for utility). |
| **Normalized values** | `quantity_normalized`, `unit_normalized` | Canonicalized to base units (liters, kWh, km, kg). Conversion logic lives in `normalizers.py`. |
| **Computed emission** | `co2e_kg` | Calculated at ingestion: `quantity_normalized × EmissionFactor.factor_kg_co2e_per_unit`. `NULL` if no matching factor exists. |
| **Classification** | `scope` (SCOPE_1/2/3), `category` (diesel, electricity_us, flight_long_haul, etc.), `source_type` | Drives reporting and dashboard aggregation. |
| **Review workflow** | `status` (PENDING → APPROVED/FLAGGED/REJECTED), `reviewed_by`, `reviewed_at`, `flag_reason` | Analysts review records; once **APPROVED**, a record is **locked for audit** — further edits are blocked at the API level. |
| **Anomaly detection** | `is_anomaly`, `anomaly_reason` | Rule-based flags set at ingestion (missing distances, estimated reads, unmapped plant codes, unknown fuel categories). |
| **Context** | `facility_code`, `facility_name`, `vendor_or_provider`, `activity_date`, `description` | Human-readable context for review. |

### 2. `UploadBatch` — Ingestion Provenance

Every file upload creates a batch that tracks:
- **`file_hash`** (SHA-256): Prevents duplicate uploads — a re-uploaded CSV returns `409 Conflict`.
- **`status`**: `PROCESSING` → `COMPLETED` | `PARTIAL` | `FAILED`.
- **`error_log`** (JSON): Per-row error messages keyed by source row number.
- **`total_rows`, `success_rows`, `error_rows`**: Ingestion summary.

### 3. `DataSource` — Source Registry

Enum-driven source types:
- `SAP_FUEL` / `SAP_PROCUREMENT` → Scope 1 (stationary/mobile combustion)
- `UTILITY_ELECTRICITY` → Scope 2 (purchased electricity)
- `TRAVEL_FLIGHT` / `TRAVEL_HOTEL` / `TRAVEL_GROUND` → Scope 3 Cat. 6 (business travel)

Each source is tenant-scoped, allowing different organizations to configure their own source labels.

### 4. `FacilityMapping` — SAP Plant Code Resolution

SAP exports contain opaque plant codes (e.g., `DE01`, `DE02`). This lookup table maps them to human-readable facility names, cities, and countries. **Unmapped codes trigger an anomaly flag** during ingestion, surfacing to the analyst as "Unmapped SAP plant code (WERKS=DE06)".

### 5. `EmissionFactor` — Conversion Factors

Standalone lookup table matching `(category, unit)` → `factor_kg_co2e_per_unit`. Factors are sourced from DEFRA 2024 and EPA eGRID 2023. The table supports `valid_from` / `valid_to` date ranges for future versioning.

16 factors are seeded across all three scopes (diesel, gasoline, biodiesel, heating oil, natural gas, LPG, kerosene, adblue, electricity, flight short/medium/long haul, hotel night, taxi, rental car).

---

## Multi-Tenancy Strategy

We use a **shared-schema, row-level isolation** approach:

1. **`TenantModel`** (abstract): Every data table inherits an `organization` FK.
2. **`TenantManager`**: Custom manager providing `.for_organization(org)` — the default queryset method used by all views.
3. **`TenantMiddleware`**: Extracts `request.organization` from the authenticated user's JWT.

**Why not schema-per-tenant?** For a 4-day prototype with SQLite/Postgres, `django-tenants` adds complexity without proportional value. The tradeoff is documented in `TRADEOFFS.md`.

---

## Scope 1/2/3 Categorization

Scope assignment is **deterministic from the data source**, not from the data itself:

| Source Type | Scope | Rationale |
|-------------|-------|-----------|
| SAP_FUEL / SAP_PROCUREMENT | Scope 1 | Direct combustion of owned/controlled fuels |
| UTILITY_ELECTRICITY | Scope 2 | Purchased electricity (location-based) |
| TRAVEL_* | Scope 3 Cat. 6 | Business travel — indirect emissions |

Each parser's `get_scope()` method returns the appropriate scope constant.

---

## Unit Normalization Pipeline

The `normalizers.py` module converts raw units to canonical base units through a two-step process:

1. **SAP unit resolution**: Maps internal SAP codes (`TO` → tonne, `KG` → kg, `M3` → m³, `ST` → piece) to normalizer-friendly strings.
2. **Canonical conversion**: Converts to base units — liters (volume), kWh (energy), km (distance), kg (mass), night (count).

This separation ensures that `quantity_original + unit_original` always reflects the source file, while `quantity_normalized + unit_normalized` drives emission calculations.

---

## Audit Trail

`django-simple-history` is attached to `ActivityRecord`. Every state change (PENDING → APPROVED, flag reason edits) creates a timestamped historical snapshot recording *who* changed *what* and *when*. This is essential for ESG reporting which must withstand financial-grade audits.
