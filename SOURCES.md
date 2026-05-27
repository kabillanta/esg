# Data Source Research & Mapping

For each of the three sources: what real-world format we researched, what we learned, what our sample data looks like and why, and what would break in a real deployment.

---

## 1. SAP — Fuel & Procurement (Scope 1)

### What we researched
SAP ERP systems (ECC 6.0 and S/4HANA) expose data through four mechanisms:
- **IDocs** — XML message envelopes for EDI/ALE integration. Overly verbose for reporting.
- **BAPIs/RFCs** — Programmatic function calls requiring SAP JCo (Java Connector) or PyRFC.
- **OData (SAP Gateway)** — RESTful API, but requires service activation on the SAP side, which IT teams gate behind months of approval.
- **Flat-file ALV exports** — The most common method. Users run transactions like `MB51` (Material Document List) or `ME2M` (Purchase Orders by Material), then click *List → Export → Spreadsheet*.

### Format chosen: Flat-file CSV export
**Justification:** This is how sustainability teams actually receive data today. The SAP admin runs a report, exports it, and emails the CSV. No middleware, no VPN, no RFC connection.

### What our sample data looks like and why

Our `sap_fuel_export.csv` uses SAP's **technical field names** as headers:

| Column | SAP Name | Meaning | Realistic quirk |
|--------|----------|---------|-----------------|
| `WERKS` | Plant | Plant code (DE01, DE02…) | Opaque codes — meaningless without a lookup table |
| `MATNR` | Material | 18-digit material number | Zero-padded, never human-readable |
| `TXZ01` | Short Text | Free-form material description | In German: "Diesel Kraftstoff", "Heizöl EL", "Erdgas (CNG)" |
| `MENGE` | Quantity | Consumption amount | **German decimal format**: `12.500,00` (periods for thousands, commas for decimals) |
| `MEINS` | Unit | SAP internal unit code | `L`, `GAL`, `KG`, `TO` (tonne), `M3` |
| `BUDAT` | Posting Date | Date of consumption | **YYYYMMDD** without dashes: `20240315` |
| `LIFNR` | Vendor | Vendor number | 10-digit padded number |

We intentionally included:
- **10+ fuel types** in German (Diesel Kraftstoff, Super Benzin, Heizöl EL, Erdgas, Flüssiggas, Kerosin, AdBlue, Bio Diesel, Super E10)
- **Mixed units** (liters and gallons in the same file)
- **Invalid rows** (non-numeric quantity `invalid_qty`, unparseable date `invalid_date`)
- **Unmapped plant codes** (DE06–DE10 have no facility mapping, triggering anomaly flags)
- **Edge-case materials** (AdBlue is not a fuel — it has zero emission factor)

### What would break in a real deployment
1. **Localized headers**: Some SAP configurations export German headers (`Menge` instead of `MENGE`, `Werk` instead of `WERKS`). We'd need a header-mapping layer.
2. **Multiple movement types**: Our parser assumes all rows are consumption. In reality, SAP exports may include returns (movement type 202), transfers (301/302), and scrapping (551). We'd need movement-type filtering.
3. **Material master complexity**: We derive fuel category from free-text `TXZ01`. In production, we'd cross-reference against the material master (MARA table) for deterministic categorization.
4. **Multi-currency pricing**: `NETPR`/`WAERS` columns contain prices in EUR and USD. We ignore pricing, but a real deployment might need spend-based emission calculations.

---

## 2. Utility Data — Electricity (Scope 2)

### What we researched
Facilities teams receive electricity data through:
- **PDF bills** — Arrive monthly, every utility formats them differently. OCR parsing (Tesseract, AWS Textract) is brittle and error-prone.
- **Portal CSV exports** — Most major utilities (ConEd, PG&E, Duke Energy, AEP) offer a "Download Usage Data" button in their customer portal.
- **Green Button / ESPI API** — A standardized XML API mandated in some US states. Coverage is inconsistent.
- **Third-party aggregators** — Urjanet (now Arcadia) and Measurabl aggregate utility data via API. Enterprise pricing ($15K+/year).

### Format chosen: Portal CSV export
**Justification:** Universal availability, exact structured data, zero OCR errors. Matches the real workflow: facilities manager logs into portal monthly, downloads CSV, forwards to sustainability team.

### What our sample data looks like and why

Our `utility_electricity.csv` mirrors a typical US utility portal export:

| Column | Meaning | Realistic quirk |
|--------|---------|-----------------|
| `Account Number` | Utility account | One account may have multiple meters |
| `Meter ID` | Physical meter | Maps to a facility/building |
| `Service Address` | Location text | Unstructured — no ZIP, no geocoding |
| `Billing Start Date` / `Billing End Date` | Billing period | **Does NOT align with calendar months**: Jan 15 – Feb 14 |
| `Total kWh` | Consumption | Comma-formatted: `45,230` |
| `Peak Demand kW` | Peak load | Not consumption — must not be added to kWh |
| `Read Type` | Actual vs. Estimated | Estimated reads are flagged as anomalies |
| `Total Charges ($)` | Dollar amount | Stored in metadata, not used for carbon calc |
| `Rate Schedule` | Tariff name | Commercial-TOU, Industrial, DataCenter-TOU |

We intentionally included:
- **Cross-month billing periods** (Jan 15 – Feb 14) to test the proration engine
- **Calendar-aligned periods** (Feb 1 – Feb 29) to test the no-proration path
- **Estimated reads** (`Read Type = Estimated`) to test anomaly flagging
- **Invalid dates** (`invalid_date`) to test error handling
- **Data center scale** (320,500 kWh) alongside small office scale (12,500 kWh)
- **Multiple accounts and meters** to test per-facility tracking

### What would break in a real deployment
1. **Regional date formats**: UK utilities use DD/MM/YYYY, not MM/DD/YYYY. The parser would need locale detection or configuration.
2. **Non-kWh units**: Gas utilities report in therms or CCF; solar exports report in kWh but need separate treatment (net metering). Our parser currently only handles kWh/MWh.
3. **Grid emission factor variation**: We apply a single national average (0.38 kg/kWh). Real deployments need eGRID subregion factors (varies from 0.08 to 0.82 kg/kWh across the US).
4. **Overlapping billing periods**: If two bills for the same meter have overlapping dates (e.g., a corrected bill), the proration engine would double-count. We'd need overlap detection.

---

## 3. Corporate Travel — Flights, Hotels, Ground Transport (Scope 3)

### What we researched
- **SAP Concur**: Offers a Standard Accounting Extract (SAE) — a flat CSV file containing all expense line items. Also has a REST API (Expense v3/v4) requiring OAuth 2.0 with company-level JWT tokens.
- **Navan (TripActions)**: REST API with travel-specific endpoints. Provides booking-level data including PNR, cabin class, and itinerary legs.
- **Manual expense reports**: Some companies still use Excel-based T&E tracking.

### Format chosen: Concur Standard Accounting Extract (CSV)
**Justification:** The SAE is the most widely used data extract format across enterprise travel platforms. It blends flights, hotels, and ground transport into a single flat file — which is exactly the parsing challenge the assignment tests. API integration would demonstrate OAuth plumbing but not parsing complexity.

### What our sample data looks like and why

Our `travel_expenses.csv` mirrors a Concur SAE:

| Column | Meaning | Realistic quirk |
|--------|---------|-----------------|
| `Report ID` | Expense report | Groups multiple line items from one trip |
| `Employee Name` | Traveler | PII — not used in calculations |
| `Expense Type` | Category | Free-text: "Airfare", "Hotel", "Car Rental", "Taxi", "Ground Transport" |
| `Transaction Date` | Trip date | ISO format: `2024-03-15` |
| `Amount` / `Currency` | Spend | Multi-currency (USD, EUR, GBP, INR, JPY) — not used for carbon calc |
| `Origin` / `Destination` | IATA codes | Only populated for flights; often missing |
| `Distance (miles)` | Travel distance | **Frequently empty** — ~30% of rows have no distance |
| `Travel Class` | Cabin | Economy, Business — affects emission factor in production |

We intentionally included:
- **Airport-code-only flights** (e.g., LHR→CDG with no distance) to test Haversine lookup
- **Distance-provided flights** (SFO→JFK with 2586 miles) to test direct conversion
- **Zero-distance ground transport** (Taxi with no distance) to test anomaly flagging
- **Short-haul** (FRA→AMS, 225mi), **medium-haul** (DXB→BOM), and **long-haul** (MAD→JFK) flights to test distance bucketing
- **Multi-currency** expenses (USD, EUR, GBP, INR, JPY)
- **Mixed expense types** in one report (flight + hotel + taxi for the same trip)
- **Invalid dates** to test error handling

### What would break in a real deployment
1. **Multi-leg flights**: A SFO→ORD→JFK itinerary shows up as one expense line. We'd need to split it into legs (SFO→ORD = medium-haul, ORD→JFK = short-haul) using PNR/itinerary data.
2. **Cabin class emission multipliers**: Business class has ~2.9× the emissions of economy (DEFRA methodology) due to larger seat footprint. We currently ignore Travel Class.
3. **Radiative Forcing Index (RFI)**: Aviation emissions at altitude have a greater warming effect than ground-level CO₂. DEFRA recommends an RFI multiplier of 1.9× for flights. We don't apply this.
4. **Airport coverage**: Our lookup table has ~45 airports. A real deployment needs the full OpenFlights database (~7,000 airports) loaded into a database table.
5. **Non-flight categories**: Rail travel (Eurostar, Amtrak) and ferry crossings would need their own parsers and emission factors.
