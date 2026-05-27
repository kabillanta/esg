import os
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from records.models import ActivityRecord

def export_records():
    records = ActivityRecord.objects.all()
    output_data = []
    
    for r in records:
        output_data.append({
            "id": str(r.id),
            "organization_id": str(r.organization.id),
            "upload_batch_id": str(r.upload_batch.id) if r.upload_batch else None,
            "source_type": r.source_type,
            "scope": r.scope,
            "category": r.category,
            "activity_date": r.activity_date.isoformat() if r.activity_date else None,
            "quantity_original": str(r.quantity_original) if r.quantity_original else None,
            "unit_original": r.unit_original,
            "quantity_normalized": str(r.quantity_normalized) if r.quantity_normalized else None,
            "unit_normalized": r.unit_normalized,
            "co2e_kg": str(r.co2e_kg) if r.co2e_kg else None,
            "is_anomaly": r.is_anomaly,
            "anomaly_reason": r.anomaly_reason,
            "status": r.status,
            "raw_data": r.raw_data
        })
        
    output_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output_schema.json')
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Successfully exported {len(output_data)} records to {output_file}")

if __name__ == "__main__":
    export_records()
