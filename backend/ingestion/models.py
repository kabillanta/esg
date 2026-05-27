import uuid
from django.db import models
from core.models import TenantModel

class DataSource(TenantModel):
    class SourceType(models.TextChoices):
        SAP_FUEL = 'SAP_FUEL', 'SAP Fuel'
        SAP_PROCUREMENT = 'SAP_PROCUREMENT', 'SAP Procurement'
        UTILITY_ELECTRICITY = 'UTILITY_ELECTRICITY', 'Utility Electricity'
        TRAVEL_FLIGHT = 'TRAVEL_FLIGHT', 'Travel Flight'
        TRAVEL_HOTEL = 'TRAVEL_HOTEL', 'Travel Hotel'
        TRAVEL_GROUND = 'TRAVEL_GROUND', 'Travel Ground'

    source_type = models.CharField(max_length=50, choices=SourceType.choices)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class FacilityMapping(TenantModel):
    """
    Lookup table to resolve SAP plant codes (WERKS) to human-readable
    facility names and locations.  Rows with unmapped WERKS codes are
    flagged as anomalies during ingestion.
    """
    plant_code = models.CharField(max_length=10, help_text="SAP WERKS plant code")
    facility_name = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('organization', 'plant_code')

    def __str__(self):
        return f"{self.plant_code} → {self.facility_name}"


class UploadBatch(TenantModel):
    class Status(models.TextChoices):
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        PARTIAL = 'PARTIAL', 'Partial'

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='upload_batches')
    uploaded_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, related_name='upload_batches')
    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, blank=True) # SHA-256 for dedup
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    total_rows = models.IntegerField(default=0)
    success_rows = models.IntegerField(default=0)
    error_rows = models.IntegerField(default=0)
    error_log = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.file_name} - {self.status}"
