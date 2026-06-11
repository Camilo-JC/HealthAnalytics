import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('django')


class ETLRequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            if duration > 1:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )
        return response


class AuditMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        request._audit_view = view_func.__name__ if hasattr(view_func, '__name__') else str(view_func)
        return None


class RoleBasedAccessMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            from .rbac import ROLE_PERMISSIONS, get_role_label
            request.user_permissions = ROLE_PERMISSIONS.get(request.user.role, [])
            request.user_role_label = get_role_label(request.user.role)
        return None

    def process_response(self, request, response):
        return response
