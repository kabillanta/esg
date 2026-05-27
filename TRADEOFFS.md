# Tradeoffs & Production Path

Given the 4-day limit, several conscious tradeoffs were made. Here are three things we deliberately did not build, why, and how they'd scale in production.

---

## 1. Synchronous File Processing (no Celery/task queue)

**Current State:** When a user uploads a CSV, the Django view parses the file, normalizes units, calculates emissions, and inserts rows synchronously within a single HTTP request/response cycle.

**The Tradeoff:** This works for our sample files (20 rows, < 5 KB). But a real SAP export could contain 50,000 rows across 40 plants. At that scale, the HTTP request would timeout (Render/Railway enforce 30–60s limits), the browser spinner would hang, and the user would assume the upload failed.

**Production Path:** Move file processing to an asynchronous task queue using **Celery + Redis**. The upload endpoint would:
1. Accept the file and create an `UploadBatch` with status `PROCESSING`.
2. Return `202 Accepted` with the batch ID immediately.
3. Dispatch a Celery task that processes rows in chunked batches of 1,000.
4. The React frontend would poll `/api/ingestion/batches/{id}/` (or use WebSockets) to show a live progress bar.

**Why we skipped it:** Celery + Redis adds infrastructure complexity (a worker process, a broker, health monitoring). For a prototype demonstrating parsing logic, synchronous processing proves the same engineering while keeping the stack simple to deploy.

---

## 2. Shared-DB Multi-Tenancy (no Row-Level Security)

**Current State:** Every model inherits a `TenantModel` with an `organization` FK. Isolation is enforced at the application layer via `TenantManager.for_organization()` and `TenantMiddleware`.

**The Tradeoff:** If a developer writes a raw ORM query and forgets `.for_organization()`, data leaks across tenants. There is no database-level safety net. In a single-developer prototype this is manageable; in a team of 10, it's a ticking bomb.

**Production Path:** Two options, depending on client scale:
- **PostgreSQL Row-Level Security (RLS):** Set a session variable (`SET app.current_org = 'uuid'`) per request in middleware, and apply RLS policies that filter on `organization_id`. This enforces isolation at the database engine level — even raw SQL cannot bypass it.
- **Schema-per-tenant** via `django-tenants`: Each organization gets its own PostgreSQL schema. Provides the strongest isolation but complicates migrations and connection pooling.

**Why we skipped it:** RLS requires PostgreSQL (not SQLite) and careful policy management. `django-tenants` adds significant migration complexity. For a demo with a single tenant, the application-layer approach is correct and sufficient.

---

## 3. Geographic Emission Factor Resolution (single national average)

**Current State:** We use a single `electricity_us` emission factor (0.38 kg CO₂e/kWh) from the EPA eGRID 2023 national average. All 16 emission factors are hardcoded in a seed script.

**The Tradeoff:** In reality, the carbon intensity of electricity varies dramatically by region. The ERCOT grid (Texas) emits ~0.42 kg/kWh; the Pacific Northwest (hydro-heavy) emits ~0.08 kg/kWh. Using a national average overstates emissions for clean-grid clients and understates for coal-grid clients by up to 5×.

Similarly, our flight emission factors don't account for cabin class (business class has ~3× the footprint of economy due to seat space allocation), and hotel factors don't vary by country.

**Production Path:**
- **Electricity:** Integrate with the EPA eGRID subregion database. Map each facility's ZIP code to its eGRID subregion, then apply the subregion-specific factor. Alternatively, integrate with **Climatiq** or **Emission Factors API** for global coverage.
- **Flights:** Apply cabin-class multipliers (economy = 1×, premium economy = 1.6×, business = 2.9×, first = 4× per DEFRA methodology).
- **Hotels:** Use country-specific factors from DEFRA's hotel accommodation dataset.
- **Versioning:** Emission factors change annually. The `EmissionFactor` model already has `valid_from` / `valid_to` fields for future time-range matching.

**Why we skipped it:** Building a geographic factor resolution system (ZIP → subregion mapping, country lookups, cabin-class multipliers) is a feature in itself. For a prototype, demonstrating the architecture — a separate `EmissionFactor` table with category+unit matching — proves we understand the pattern. The hardcoded factors are placeholders, not the design.
