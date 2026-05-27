import django_filters
from .models import ActivityRecord

class ActivityRecordFilter(django_filters.FilterSet):
    activity_date_after = django_filters.DateFilter(field_name='activity_date', lookup_expr='gte')
    activity_date_before = django_filters.DateFilter(field_name='activity_date', lookup_expr='lte')

    class Meta:
        model = ActivityRecord
        fields = ['scope', 'source_type', 'status', 'is_anomaly', 'upload_batch']
