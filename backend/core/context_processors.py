from django.conf import settings
from .rbac import get_role_label, ROLE_PERMISSIONS, MODULES


def site_settings(request):
    ctx = {
        'site_name': settings.SITE_NAME,
        'site_description': settings.SITE_DESCRIPTION,
        'debug': settings.DEBUG,
    }
    if request.user.is_authenticated:
        ctx['user_role'] = request.user.role
        ctx['user_role_label'] = get_role_label(request.user.role)
        ctx['user_permissions'] = ROLE_PERMISSIONS.get(request.user.role, [])
    return ctx
