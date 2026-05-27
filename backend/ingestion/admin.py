from django.contrib import admin
from .models import DataSource, UploadBatch, FacilityMapping

admin.site.register(DataSource)
admin.site.register(UploadBatch)
admin.site.register(FacilityMapping)
