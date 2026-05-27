from django.db import models

class TenantManager(models.Manager):
    """
    Manager for TenantModel.
    Provides a convenience method to filter querysets by organization.
    """
    def for_organization(self, org):
        if not org:
            return self.none()
        return self.filter(organization=org)
