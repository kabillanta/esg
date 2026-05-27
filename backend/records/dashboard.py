from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import ActivityRecord

class DashboardStatsView(APIView):
    def get(self, request):
        qs = ActivityRecord.objects.for_organization(request.user.organization)
        
        total_co2e = qs.aggregate(total=Sum('co2e_kg'))['total'] or 0
        
        scope_breakdown = qs.values('scope').annotate(
            total_co2e=Sum('co2e_kg'),
            count=Count('id')
        )
        
        source_breakdown = qs.values('source_type').annotate(
            total_co2e=Sum('co2e_kg'),
            count=Count('id')
        )
        
        status_breakdown = qs.values('status').annotate(
            count=Count('id')
        )
        
        anomalies_count = qs.filter(is_anomaly=True).count()
        pending_count = qs.filter(status='PENDING').count()
        
        return Response({
            'total_co2e_kg': total_co2e,
            'scope_breakdown': list(scope_breakdown),
            'source_breakdown': list(source_breakdown),
            'status_breakdown': list(status_breakdown),
            'anomalies_count': anomalies_count,
            'pending_review_count': pending_count
        })
