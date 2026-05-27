import hashlib
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from .models import DataSource, UploadBatch
from .serializers import FileUploadSerializer, UploadBatchSerializer
from .parsers.sap_fuel import SAPFuelParser
from .parsers.utility import UtilityParser
from .parsers.travel import TravelParser

class UploadView(APIView):
    """
    Accepts a CSV file, parses it synchronously within a transaction, and saves the batch.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        file = serializer.validated_data['file']
        data_source_id = serializer.validated_data['data_source_id']

        try:
            data_source = DataSource.objects.for_organization(request.user.organization).get(id=data_source_id)
        except DataSource.DoesNotExist:
            return Response({'error': 'Data source not found'}, status=404)

        # Enforce 5MB limit
        if file.size > 5 * 1024 * 1024:
            return Response({'error': 'File too large. Max 5MB allowed.'}, status=400)

        # Decode file
        file_content = file.read().decode('utf-8')

        # ── Deduplication via SHA-256 file hash ──────────────────────
        file_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
        if UploadBatch.objects.filter(
            organization=request.user.organization,
            file_hash=file_hash,
        ).exists():
            return Response(
                {'error': 'This file has already been uploaded (duplicate hash).'},
                status=409,
            )

        try:
            with transaction.atomic():
                batch = UploadBatch.objects.create(
                    organization=request.user.organization,
                    data_source=data_source,
                    uploaded_by=request.user,
                    file_name=file.name,
                    file_hash=file_hash,
                    status='PROCESSING'
                )

                if data_source.source_type in ('SAP_FUEL', 'SAP_PROCUREMENT'):
                    parser = SAPFuelParser(batch)
                elif data_source.source_type == 'UTILITY_ELECTRICITY':
                    parser = UtilityParser(batch)
                elif data_source.source_type in ('TRAVEL_FLIGHT', 'TRAVEL_HOTEL', 'TRAVEL_GROUND'):
                    parser = TravelParser(batch)
                else:
                    raise ValueError(f"Unknown source type {data_source.source_type}")

                parser.process_file(file_content)
                
                # If everything failed, we could raise exception to rollback, but we want to keep the error log
                # The batch is saved with 'FAILED' status in the parser if no rows succeed.
                
        except Exception as e:
            # Fatal error rollback
            return Response({'error': str(e)}, status=500)

        return Response(UploadBatchSerializer(batch).data)

class DataSourceListView(APIView):
    def get(self, request):
        sources = DataSource.objects.for_organization(request.user.organization)
        from .serializers import DataSourceSerializer
        return Response(DataSourceSerializer(sources, many=True).data)

class UploadBatchListView(APIView):
    def get(self, request):
        batches = UploadBatch.objects.for_organization(request.user.organization).order_by('-created_at')
        return Response(UploadBatchSerializer(batches, many=True).data)
