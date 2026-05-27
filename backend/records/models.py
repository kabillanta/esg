import uuid
from django.db import models
from core.models import TenantModel
from simple_history.models import HistoricalRecords

class ActivityRecord(TenantModel):
    class Scope(models.TextChoices):
        SCOPE_1 = 'SCOPE_1', 'Scope 1'
        SCOPE_2 = 'SCOPE_2', 'Scope 2'
        SCOPE_3 = 'SCOPE_3', 'Scope 3'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        FLAGGED = 'FLAGGED', 'Flagged'
        REJECTED = 'REJECTED', 'Rejected'

    upload_batch = models.ForeignKey('ingestion.UploadBatch', on_delete=models.CASCADE, related_name='records')
    source_type = models.CharField(max_length=50) # Denormalized from DataSource
    scope = models.CharField(max_length=20, choices=Scope.choices)

    # Source identity
    source_row_number = models.IntegerField()
    raw_data = models.JSONField(default=dict, blank=True)

    # Normalized fields
    activity_date = models.DateField()
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    quantity_original = models.DecimalField(max_digits=19, decimal_places=4)
    unit_original = models.CharField(max_length=50)
    quantity_normalized = models.DecimalField(max_digits=19, decimal_places=4)
    unit_normalized = models.CharField(max_length=50)
    co2e_kg = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)

    # Location / context
    facility_code = models.CharField(max_length=100, blank=True)
    facility_name = models.CharField(max_length=255, blank=True)
    vendor_or_provider = models.CharField(max_length=255, blank=True)

    # Review workflow
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    flag_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_records')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Anomaly detection
    is_anomaly = models.BooleanField(default=False)
    anomaly_reason = models.TextField(blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.category} - {self.activity_date} ({self.status})"

class EmissionFactor(models.Model):
    category = models.CharField(max_length=100, unique=True)
    scope = models.CharField(max_length=20, choices=ActivityRecord.Scope.choices)
    factor_kg_co2e_per_unit = models.DecimalField(max_digits=19, decimal_places=6)
    unit = models.CharField(max_length=50)
    source_reference = models.CharField(max_length=255, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.category} ({self.factor_kg_co2e_per_unit} kgCO2e/{self.unit})"
