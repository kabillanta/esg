from abc import ABC, abstractmethod
import csv
from io import StringIO
from django.db import transaction
from records.models import ActivityRecord, EmissionFactor
from ingestion.normalizers import normalize_quantity_and_unit
from ingestion.anomaly import detect_anomaly

class BaseParser(ABC):
    def __init__(self, upload_batch):
        self.upload_batch = upload_batch
        self.organization = upload_batch.organization
        self.source_type = upload_batch.data_source.source_type
        
    @abstractmethod
    def get_scope(self):
        pass
        
    @abstractmethod
    def parse_row(self, row):
        """
        Parses a single row (dict).
        Returns either:
          - a dict of normalized fields for ActivityRecord, or
          - a list of dicts (e.g. utility proration producing multiple records
            from a single CSV row).
        Raises ValueError if the row is fatally invalid (e.g., missing critical field).
        """
        pass
        
    def process_file(self, file_content):
        """
        Processes a CSV string. Uses transaction.atomic() at the caller level.
        """
        reader = csv.DictReader(StringIO(file_content))
        
        records_to_create = []
        error_log = {}
        row_count = 0
        success_count = 0
        error_count = 0
        
        # Pre-fetch emission factors for performance
        factors = list(EmissionFactor.objects.filter(scope=self.get_scope()))
        
        def calculate_co2e(category, quantity, unit):
            for factor in factors:
                if factor.category == category and factor.unit == unit:
                    return quantity * factor.factor_kg_co2e_per_unit
            return None
            
        for i, row in enumerate(reader):
            row_count += 1
            source_row_number = i + 2 # +1 for 0-index, +1 for header
            
            try:
                result = self.parse_row(row)

                # Normalise to a list so we can handle both single-record
                # and multi-record (proration) returns uniformly.
                if isinstance(result, dict):
                    parsed_items = [result]
                elif isinstance(result, list):
                    parsed_items = result
                else:
                    raise ValueError("parse_row must return a dict or list of dicts")

                for parsed_data in parsed_items:
                    # Normalization
                    qty_norm, unit_norm, hint = normalize_quantity_and_unit(
                        parsed_data['quantity_original'], 
                        parsed_data['unit_original']
                    )
                    
                    parsed_data['quantity_normalized'] = qty_norm
                    parsed_data['unit_normalized'] = unit_norm
                    
                    if hint and 'category' not in parsed_data:
                        parsed_data['category'] = hint
                        
                    # Calculate CO2e if possible
                    parsed_data['co2e_kg'] = calculate_co2e(
                        parsed_data['category'], 
                        qty_norm, 
                        unit_norm
                    )
                    
                    # Anomaly detection
                    is_anomaly, anomaly_reason = detect_anomaly(row, parsed_data, self.source_type)

                    # Check for unmapped WERKS hint from SAP parser
                    if parsed_data.pop('_unmapped_werks', False):
                        is_anomaly = True
                        werks = parsed_data.get('facility_code', '?')
                        extra = f"Unmapped SAP plant code (WERKS={werks})"
                        anomaly_reason = f"{anomaly_reason}; {extra}" if anomaly_reason else extra

                    parsed_data['is_anomaly'] = is_anomaly
                    parsed_data['anomaly_reason'] = anomaly_reason
                    
                    record = ActivityRecord(
                        organization=self.organization,
                        upload_batch=self.upload_batch,
                        source_type=self.source_type,
                        scope=self.get_scope(),
                        source_row_number=source_row_number,
                        raw_data=row,
                        **parsed_data
                    )
                    records_to_create.append(record)

                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_log[str(source_row_number)] = str(e)
                
        # Bulk create for performance
        if records_to_create:
            ActivityRecord.objects.bulk_create(records_to_create)
            
        self.upload_batch.total_rows = row_count
        self.upload_batch.success_rows = success_count
        self.upload_batch.error_rows = error_count
        self.upload_batch.error_log = error_log

        if success_count == 0 and error_count > 0:
            self.upload_batch.status = 'FAILED'
        elif error_count > 0:
            self.upload_batch.status = 'PARTIAL'
        else:
            self.upload_batch.status = 'COMPLETED'
            
        self.upload_batch.save()
