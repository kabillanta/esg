from rest_framework import serializers
from .models import DataSource, UploadBatch

class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = '__all__'

class UploadBatchSerializer(serializers.ModelSerializer):
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = UploadBatch
        fields = '__all__'

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    data_source_id = serializers.UUIDField()
