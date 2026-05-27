# Architecture Decisions

Every ambiguity we resolved, what we chose, why, and what we'd ask the PM if we could.

---

## 1. Authentication: The "Demo Mode" Shortcut
**Decision:** We built a "Role Switcher" dropdown in the navigation bar instead of a traditional Login/Signup flow.
**Why:** The assignment explicitly stated Auth was low priority. A full auth flow (login, password reset, email verification, JWT refresh logic) would consume 20–30% of the 4-day timeframe. By pre-seeding an Admin and an Analyst user, and swapping their JWTs on the fly via `/api/auth/demo-token/`, we perfectly simulate authenticated roles without the UI overhead.
**What we'd ask the PM:** "Do your clients use SSO (Okta, Azure AD)? If so, we'd integrate SAML/OIDC rather than building a custom auth form."

## 2. SAP Subset: Material Consumption Flat Files over OData/IDoc
**Decision:** We chose to ingest SAP data as **flat-file CSV exports** using SAP's standard technical field names (WERKS, MATNR, TXZ01, MENGE, MEINS, BUDAT, etc.).
**Why:**
- **IDocs** are XML-based message envelopes designed for system-to-system integration — overly complex for pulling consumption reports.
- **OData** (via SAP Gateway) requires a dedicated RFC destination, service activation on the SAP side, and VPN tunnelling — enterprise IT teams take months to approve this.
- **BAPI** calls require an RFC connection and SAP JCo library, which introduces Java dependencies.
- **Flat files** are what 90% of sustainability teams actually receive: someone runs transaction MB51 or a custom Z-report, hits "Export to Spreadsheet", and emails it.

**What we handle:** German decimal formats (`12.500,00`), SAP internal date format (`YYYYMMDD`), unit codes (`L`, `GAL`, `KG`, `TO`, `M3`), and 10+ fuel categories extracted from the free-form TXZ01 short text (Diesel, Benzin, Heizöl, Erdgas, Flüssiggas, Kerosin, AdBlue, Bio Diesel, Super E10).
**What we ignore:** SAP movement types (we assume all rows are consumption), cost center hierarchies, and currency conversion.
**What we'd ask the PM:** "Which SAP transaction are your clients' procurement teams running? ME2M? MB51? A custom Z-report? This determines the exact column set."

## 3. Utility Data: Portal CSV over PDF Scraping
**Decision:** We parse CSV exports from utility portals (like ConEd's "Download Usage Data").
**Why:** PDF bill scraping via OCR is extraordinarily brittle — every utility formats bills differently, and layouts change quarterly. CSV exports provide exact structured data. API integrations (Urjanet/Arcadia) cost $15K+/year and have limited global coverage.
**What we'd ask the PM:** "Do your clients have utility accounts across multiple states? If so, we'd need to apply region-specific eGRID emission factors rather than a single national average."

## 4. Billing Period Proration
**Decision:** When a utility bill spans two calendar months (e.g., Jan 15 – Feb 14), we **split the bill into multiple ActivityRecords**, one per calendar month, with quantities prorated by day count.
**Why:** ESG reporting is always calendar-aligned (Q1, Q2, etc.). Dumping a cross-month bill entirely into one month skews monthly comparisons and makes quarterly audits unreliable.
**Alternative considered:** Store the raw billing period and prorate at report-generation time. We chose ingestion-time proration because it keeps the reporting layer simple and stateless.
**What we'd ask the PM:** "Do clients want to see the original bill row alongside the prorated breakdown, or just the prorated records?"

## 5. Travel: Concur-style CSV with Airport Distance Lookup
**Decision:** We parse Concur Standard Accounting Extract (SAE) format CSVs. When `Distance (miles)` is empty and IATA airport codes are present, we calculate great-circle distance using the Haversine formula against a 40+ airport coordinate database.
**Why:** Concur/Navan APIs require OAuth developer app registration per client. For a prototype, CSV is faster to integrate and demonstrates the same parsing complexity. The Haversine fallback is critical because ~30% of Concur expense reports omit the distance field.
**What we'd ask the PM:** "Do clients use a single travel platform (Concur) or multiple (Concur + Navan + direct bookings)? This determines whether we need multiple parser profiles."

## 6. Flight Distance Bucketing
**Decision:** Flights are categorized as short-haul (< 483 km / 300 mi), medium-haul (483–3700 km), or long-haul (> 3700 km / 2300 mi) per DEFRA thresholds. Each category applies a different emission factor.
**Why:** Short-haul flights produce significantly more emissions per km due to the high fuel burn during takeoff and landing relative to cruise distance. Using a single average factor would understate short-haul emissions by ~30%.

## 7. Audit Lock on Approved Records
**Decision:** Once an analyst marks a record as `APPROVED`, it becomes **immutable** — the API returns `409 Conflict` if anyone attempts to re-approve, flag, or reject it.
**Why:** ESG data that has been approved for audit must not change. If a mistake is discovered post-approval, the correct workflow is to create an adjustment entry, not edit the approved record. This mirrors financial close procedures.

## 8. UI/UX: The "Linear-style" Side Panel
**Decision:** We killed the traditional "Detail Page" route (`/records/:id`) in favor of a slide-out side panel on the main table.
**Why:** Analysts need to review 50–100 rows per batch. Navigating away from a table, clicking "Approve", and hitting the back button breaks context and destroys productivity. A slide-out panel allows rapid review of raw vs. normalized data in a dense, low-latency interface.

## 9. File Deduplication via SHA-256
**Decision:** We hash the file content (SHA-256) on upload and reject re-uploads with `409 Conflict`.
**Why:** Facilities teams often accidentally upload the same monthly bill twice, which would double-count emissions. Hash-based dedup catches this silently.
**What we'd ask the PM:** "Should we support partial re-uploads (e.g., corrected version of the same file) by allowing override? Or should the user first delete the previous batch?"
