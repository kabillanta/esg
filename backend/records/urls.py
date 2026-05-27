from django.urls import path
from .views import (
    ActivityRecordListView, 
    ActivityRecordDetailView,
    ApproveRecordView,
    FlagRecordView,
    RejectRecordView,
    EmissionFactorListView
)

urlpatterns = [
    path('', ActivityRecordListView.as_view(), name='record-list'),
    path('<uuid:pk>/', ActivityRecordDetailView.as_view(), name='record-detail'),
    path('<uuid:pk>/approve/', ApproveRecordView.as_view(), name='record-approve'),
    path('<uuid:pk>/flag/', FlagRecordView.as_view(), name='record-flag'),
    path('<uuid:pk>/reject/', RejectRecordView.as_view(), name='record-reject'),
    path('emission-factors/', EmissionFactorListView.as_view(), name='emission-factors'),
]
