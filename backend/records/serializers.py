from rest_framework import serializers
from .models import ActivityRecord, EmissionFactor

class ActivityRecordSerializer(serializers.ModelSerializer):
    upload_batch_name = serializers.CharField(source='upload_batch.file_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)

    class Meta:
        model = ActivityRecord
        fields = '__all__'

class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = '__all__'
