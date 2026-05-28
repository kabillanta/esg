# Breathe ESG: Enterprise Climate Data Platform

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)
![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

An enterprise-grade ESG (Environmental, Social, and Governance) data ingestion and auditing platform. Designed to process disparate, unstructured corporate carbon data across Scope 1, 2, and 3 emissions, normalize the outputs, and enforce a strict review-and-approval pipeline for financial compliance and external auditing.

---

## Overview

The primary friction in ESG reporting is not emission calculation; it is data acquisition and normalization. Enterprise data resides in fragmented systems, often exported in inconsistent formats by discrete operational teams. Procurement teams export German-formatted SAP material logs. Facilities managers download cross-month utility CSVs. Corporate travelers utilize platforms like Concur, frequently omitting critical travel distances.

Breathe ESG addresses this operational reality by providing a resilient ingestion layer that natively anticipates and handles the edge cases inherent in raw corporate data, bridging the gap between raw operational exports and audit-ready sustainability metrics.

## Core Capabilities

- **Resilient Data Ingestion:** Domain-specific parsers engineered to handle SAP ALV Flat Files, Utility Portal CSVs, and Concur Standard Accounting Extracts (SAE).
- **Intelligent Proration Engine:** Automatically identifies utility billing periods that span multiple calendar months and accurately prorates consumption (kWh) to align with standard quarterly/annual ESG reporting frameworks.
- **Programmatic Fallbacks:** Implements an internal IATA airport coordinate database to calculate great-circle distances via the Haversine formula when travel platforms fail to provide distance data.
- **Unit Normalization Pipeline:** Programmatically standardizes international number formats and proprietary ERP unit codes into canonical measurement standards (liters, kg, km, kWh).
- **Immutable Audit Trail:** Enforces a rigid analyst review pipeline. Once a data record is classified as `APPROVED`, it is cryptographically locked against subsequent modifications to guarantee data integrity for external auditors.
- **Multi-Tenant Architecture:** Employs row-level database isolation, ensuring strict data compartmentalization across multiple client organizations operating on shared backend infrastructure.

## Architecture & Implementation

### Backend Infrastructure
- **Framework:** Django & Django REST Framework
- **Data Persistence:** SQLite (local development) / PostgreSQL (production)
- **Compliance Tooling:** `django-simple-history` for comprehensive state-change tracking

### Frontend Interface
- **Framework:** React + TypeScript (Vite)
- **Styling:** Modular CSS utilizing modern custom properties, eliminating external UI framework bloat.
- **State Management:** Custom Axios interceptors handling JWT authentication and role-based access control.

---

## Technical Documentation

This repository contains extensive architectural documentation detailing the engineering decisions, tradeoffs, and compliance strategies implemented during development:

1. [**MODEL.md**](./MODEL.md) - Entity-relationship schemas, multi-tenancy strategy, and the unit normalization pipeline.
2. [**DECISIONS.md**](./DECISIONS.md) - Detailed rationale behind 9 major architectural choices and deployment considerations.
3. [**TRADEOFFS.md**](./TRADEOFFS.md) - Analysis of deliberate engineering compromises made for this prototype and the roadmap to production scale.
4. [**SOURCES.md**](./SOURCES.md) - Exhaustive research into SAP, Utility, and Travel data structures, defining the parameters of our sample datasets.

---

## Local Environment Setup

### 1. Backend Initialization
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Execute database migrations and seed baseline configurations
python manage.py migrate
python manage.py seed_data

# Initialize the development server
python manage.py runserver
```

### 2. Frontend Initialization
```bash
cd frontend
npm install
npm run dev
```

### 3. System Validation
1. Access the application at `http://localhost:5173`.
2. Authenticate using the **Analyst** or **Admin** role via the interface header.
3. Navigate to the **Upload** module.
4. Process any of the provided validation datasets located in `backend/sample_data/`:
   - `sap_fuel_export.csv`
   - `utility_electricity.csv`
   - `travel_expenses.csv`
5. Navigate to the **Records** module to review the normalized outputs, flag anomalies, and execute the approval workflow.

---
*Developed for the Breathe ESG Technical Assessment.*
