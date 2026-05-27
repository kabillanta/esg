from django.utils.deprecation import MiddlewareMixin

class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that extracts the organization from the currently authenticated user
    and attaches it to the request as request.organization.
    """
    def process_request(self, request):
        request.organization = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.organization = request.user.organization
