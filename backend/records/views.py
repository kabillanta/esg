from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import ActivityRecord, EmissionFactor
from .serializers import ActivityRecordSerializer, EmissionFactorSerializer
from .filters import ActivityRecordFilter
from core.permissions import IsAdmin

class ActivityRecordListView(generics.ListAPIView):
    serializer_class = ActivityRecordSerializer
    filterset_class = ActivityRecordFilter
    search_fields = ['category', 'description', 'facility_name', 'vendor_or_provider']
    ordering_fields = ['activity_date', 'co2e_kg', 'status']
    ordering = ['-activity_date']

    def get_queryset(self):
        return ActivityRecord.objects.for_organization(self.request.user.organization)

class ActivityRecordDetailView(generics.RetrieveAPIView):
    serializer_class = ActivityRecordSerializer
    
    def get_queryset(self):
        return ActivityRecord.objects.for_organization(self.request.user.organization)

class RecordActionBaseView(APIView):
    """Base class for record review actions. Only ADMINs can review."""
    permission_classes = [IsAdmin]

    def get_record(self, pk):
        try:
            return ActivityRecord.objects.for_organization(self.request.user.organization).get(pk=pk)
        except ActivityRecord.DoesNotExist:
            return None

class ApproveRecordView(RecordActionBaseView):
    def post(self, request, pk):
        record = self.get_record(pk)
        if not record:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Audit lock: once approved, a record cannot be re-approved
        if record.status == ActivityRecord.Status.APPROVED:
            return Response(
                {'error': 'Record is already approved and locked for audit.'},
                status=status.HTTP_409_CONFLICT,
            )

        record.status = ActivityRecord.Status.APPROVED
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.flag_reason = ''
        record.save()
        
        return Response(ActivityRecordSerializer(record).data)

class FlagRecordView(RecordActionBaseView):
    def post(self, request, pk):
        record = self.get_record(pk)
        if not record:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Audit lock: approved records cannot be flagged
        if record.status == ActivityRecord.Status.APPROVED:
            return Response(
                {'error': 'Record is approved and locked for audit. Cannot flag.'},
                status=status.HTTP_409_CONFLICT,
            )

        reason = request.data.get('reason', 'Flagged for review')
        record.status = ActivityRecord.Status.FLAGGED
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.flag_reason = reason
        record.save()
        
        return Response(ActivityRecordSerializer(record).data)

class RejectRecordView(RecordActionBaseView):
    def post(self, request, pk):
        record = self.get_record(pk)
        if not record:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Audit lock: approved records cannot be rejected
        if record.status == ActivityRecord.Status.APPROVED:
            return Response(
                {'error': 'Record is approved and locked for audit. Cannot reject.'},
                status=status.HTTP_409_CONFLICT,
            )

        reason = request.data.get('reason', 'Rejected by reviewer')
        record.status = ActivityRecord.Status.REJECTED
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.flag_reason = reason
        record.save()

        return Response(ActivityRecordSerializer(record).data)

class EmissionFactorListView(generics.ListAPIView):
    queryset = EmissionFactor.objects.all()
    serializer_class = EmissionFactorSerializer
