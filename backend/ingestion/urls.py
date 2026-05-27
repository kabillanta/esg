from django.urls import path
from .views import UploadView, DataSourceListView, UploadBatchListView

urlpatterns = [
    path('upload/', UploadView.as_view(), name='upload'),
    path('data-sources/', DataSourceListView.as_view(), name='data-sources'),
    path('batches/', UploadBatchListView.as_view(), name='batches'),
]
