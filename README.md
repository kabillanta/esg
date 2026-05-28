# Breathe ESG · Climate Data Platform

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)
![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

An enterprise-grade ESG data ingestion and auditing prototype. Built to ingest messy, real-world corporate carbon data (Scope 1, 2, and 3), normalize it, and provide a strict review-and-approval pipeline for sustainability analysts before handing it over to financial auditors.

---

## 🎯 The Challenge
ESG data doesn't come neatly packaged in a single API. It lives across fragmented, inconsistent sources. 
Facilities teams pull cross-month electricity CSVs from utility portals. Procurement teams email German-formatted SAP exports. Corporate travelers use Concur, often forgetting to log flight distances.

Breathe ESG solves this by providing a unified ingestion layer that natively handles the edge cases of real-world corporate data.

## ✨ Key Features

- **Robust Data Parsers:** Custom parsers for SAP Flat Files, Utility Portal CSVs, and Concur Travel Extracts.
- **Intelligent Proration Engine:** Automatically detects when a utility billing period splits across two calendar months and accurately prorates the kWh consumption by day.
- **Haversine Distance Fallback:** Uses an internal IATA airport coordinate database to calculate great-circle distances for flights when Concur extracts drop the distance field.
- **Unit Normalization Pipeline:** Seamlessly translates German number formats (`12.500,00`) and arbitrary SAP units (`TO`, `KG`, `M3`) into canonical metrics (`liters`, `kg`, `km`).
- **Immutable Audit Trail:** Analysts review and flag anomalies. Once a record is marked as `APPROVED`, it is securely locked against further edits to guarantee audit compliance.
- **Multi-Tenant Architecture:** Row-level isolation ensures multiple organizations can securely process their data on the same backend infrastructure.

## 🏗️ Architecture

### Backend
- **Framework:** Django & Django REST Framework
- **Database:** SQLite (local dev) / PostgreSQL (production)
- **Key Libraries:** `django-simple-history` for audit trails, `django-cors-headers`

### Frontend
- **Framework:** React + TypeScript via Vite
- **Styling:** Modern, Linear-inspired CSS variables (no bloated CSS frameworks)
- **State & API:** Custom Axios interceptors with JWT role-switching ("Demo Mode")

---

## 📚 Technical Documentation

This project includes extensive architectural documentation detailing the decisions and tradeoffs made during development:

1. [**MODEL.md**](./MODEL.md) - Entity-relationship schema, multi-tenancy strategy, and unit normalization pipeline.
2. [**DECISIONS.md**](./DECISIONS.md) - The 9 major architectural choices made, why we chose them, and what we'd ask the PM in a real sprint.
3. [**TRADEOFFS.md**](./TRADEOFFS.md) - Three deliberate compromises made for the 4-day prototype (e.g., synchronous processing over Celery/Redis) and the path to production.
4. [**SOURCES.md**](./SOURCES.md) - Deep-dive research into SAP, Utility, and Travel data structures, explaining exactly why our sample data contains the edge cases it does.

---

## 🚀 Running Locally

### 1. Start the Django Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run migrations and seed the database with emission factors/demo users
python manage.py migrate
python manage.py seed_data

python manage.py runserver
```

### 2. Start the React Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Test with Sample Data
1. Navigate to `http://localhost:5173`
2. Select an **Analyst** or **Admin** role in the top right.
3. Go to the **Upload** tab.
4. Upload any of the provided mock files located in `backend/sample_data/`:
   - `sap_fuel_export.csv`
   - `utility_electricity.csv`
   - `travel_expenses.csv`
5. Go to the **Records** tab to review, flag, and approve the normalized data!

---
*Developed for the Breathe ESG Technical Assessment.*
