"""
Smoke-test script: loads each sample CSV through its parser and prints
a summary.  Run with:  python manage.py shell < ingestion/smoke_test.py
"""
import os, sys

# ── Bootstrap Django ─────────────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.models import Organization, User
from ingestion.models import DataSource, UploadBatch
from ingestion.parsers.sap_fuel import SAPFuelParser
from ingestion.parsers.utility import UtilityParser
from ingestion.parsers.travel import TravelParser
from records.models import ActivityRecord

org = Organization.objects.get(slug='demo-org')
user = User.objects.get(username='admin_demo')

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath('manage.py')), 'sample_data')


def _run(source_type, parser_cls, csv_filename):
    csv_path = os.path.join(SAMPLE_DIR, csv_filename)
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()

    ds = DataSource.objects.get(organization=org, source_type=source_type)
    batch = UploadBatch.objects.create(
        organization=org,
        data_source=ds,
        uploaded_by=user,
        file_name=csv_filename,
        status='PROCESSING',
    )
    parser = parser_cls(batch)
    parser.process_file(content)
    batch.refresh_from_db()

    records = ActivityRecord.objects.filter(upload_batch=batch)
    anomalies = records.filter(is_anomaly=True)

    print(f"\n{'='*60}")
    print(f"  {source_type}  |  {csv_filename}")
    print(f"{'='*60}")
    print(f"  Status     : {batch.status}")
    print(f"  Total rows : {batch.total_rows}")
    print(f"  Success    : {batch.success_rows}")
    print(f"  Errors     : {batch.error_rows}")
    print(f"  Records    : {records.count()}")
    print(f"  Anomalies  : {anomalies.count()}")
    if batch.error_log:
        print(f"  Error log  : {batch.error_log}")
    for rec in records[:5]:
        co2 = f"{rec.co2e_kg:.2f} kgCO2e" if rec.co2e_kg else "no EF match"
        anom = " [ANOMALY]" if rec.is_anomaly else ""
        print(f"    -> {rec.category:20s}  {rec.quantity_normalized:>12.4f} {rec.unit_normalized:6s}  {co2}{anom}")
        if rec.is_anomaly:
            print(f"       Reason: {rec.anomaly_reason}")
    print()


# ── Clear previous test records ──────────────────────────────────────
ActivityRecord.objects.filter(organization=org).delete()
UploadBatch.objects.filter(organization=org).delete()

_run('SAP_FUEL',              SAPFuelParser,  'sap_fuel_export.csv')
_run('UTILITY_ELECTRICITY',   UtilityParser,  'utility_electricity.csv')
_run('TRAVEL_FLIGHT',         TravelParser,   'travel_expenses.csv')

print("\nDone.")
