from functools import wraps
from rest_framework import status
from rest_framework.response import Response


MODULES = {
    'dashboard': 'Dashboard / KPIs',
    'patients': 'Pacientes',
    'patients_manage': 'Pacientes - Crear/Editar/Eliminar',
    'patients_delete': 'Pacientes - Eliminar registros',
    'etl': 'ETL - Visualizar',
    'etl_execute': 'ETL - Ejecutar pipelines',
    'etl_delete': 'ETL - Eliminar historiales',
    'analytics': 'Analítica - Visualizar',
    'analytics_export': 'Analítica - Exportar',
    'ml': 'Machine Learning - Visualizar',
    'ml_train': 'ML - Entrenar modelos',
    'ml_predict': 'ML - Realizar predicciones',
    'reports': 'Reportes - Visualizar',
    'reports_export': 'Reportes - Exportar',
    'users_manage': 'Usuarios - Gestionar',
    'users_delete': 'Usuarios - Eliminar',
    'settings': 'Configuración - Ver',
    'settings_global': 'Configuración - Parámetros globales',
    'audit_view': 'Auditoría - Visualizar',
}

ROLE_PERMISSIONS = {
    'admin': [
        'dashboard', 'patients', 'patients_manage', 'patients_delete',
        'etl', 'etl_execute', 'etl_delete',
        'analytics', 'analytics_export',
        'ml', 'ml_train', 'ml_predict',
        'reports', 'reports_export',
        'users_manage', 'users_delete',
        'settings', 'settings_global',
        'audit_view',
    ],
    'analyst': [
        'dashboard',
        'patients',
        'etl', 'etl_execute',
        'analytics', 'analytics_export',
        'ml', 'ml_train', 'ml_predict',
        'reports', 'reports_export',
    ],
    'doctor': [
        'dashboard',
        'patients',
        'analytics',
        'reports',
        'settings',
    ],
}

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


def has_module_permission(user, module):
    if not user.is_authenticated:
        return False
    return module in ROLE_PERMISSIONS.get(user.role, [])


def require_permission(module):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response(
                    {'success': False, 'error': 'Autenticación requerida'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            if not has_module_permission(request.user, module):
                return Response(
                    {'success': False, 'error': 'No tienes permiso para acceder a este recurso'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(view_instance, request, *args, **kwargs)
        return wrapper
    return decorator


def get_role_label(role):
    labels = {'admin': 'Administrador', 'analyst': 'Analista', 'doctor': 'Doctor'}
    return labels.get(role, role)


def get_user_menu(user):
    if not user.is_authenticated:
        return []
    role = user.role
    menu_sections = {
        'admin': {
            'Principal': [
                {'url': '/', 'label': 'Dashboard', 'icon': 'bi-grid-1x2-fill'},
                {'url': '/patients/', 'label': 'Pacientes', 'icon': 'bi-people-fill'},
                {'url': '/etl/', 'label': 'ETL', 'icon': 'bi-arrow-repeat'},
            ],
            'Analítica': [
                {'url': '/analytics/', 'label': 'Analítica', 'icon': 'bi-graph-up-arrow'},
                {'url': '/ml/', 'label': 'Machine Learning', 'icon': 'bi-cpu'},
            ],
            'Reportes': [
                {'url': '/reports/', 'label': 'Reportes', 'icon': 'bi-file-text'},
            ],
            'Sistema': [
                {'url': '/settings/', 'label': 'Configuración', 'icon': 'bi-gear'},
                {'url': '/settings/#users', 'label': 'Usuarios', 'icon': 'bi-shield-lock'},
            ],
        },
        'analyst': {
            'Principal': [
                {'url': '/', 'label': 'Dashboard', 'icon': 'bi-grid-1x2-fill'},
                {'url': '/patients/', 'label': 'Pacientes', 'icon': 'bi-people-fill'},
                {'url': '/etl/', 'label': 'ETL', 'icon': 'bi-arrow-repeat'},
            ],
            'Analítica': [
                {'url': '/analytics/', 'label': 'Analítica', 'icon': 'bi-graph-up-arrow'},
                {'url': '/ml/', 'label': 'Machine Learning', 'icon': 'bi-cpu'},
            ],
        },
        'doctor': {
            'Principal': [
                {'url': '/', 'label': 'Dashboard', 'icon': 'bi-grid-1x2-fill'},
                {'url': '/patients/', 'label': 'Pacientes', 'icon': 'bi-people-fill'},
            ],
            'Analítica': [
                {'url': '/analytics/', 'label': 'Analítica', 'icon': 'bi-graph-up-arrow'},
                {'url': '/ml/', 'label': 'Machine Learning', 'icon': 'bi-cpu'},
            ],
            'Reportes': [
                {'url': '/reports/', 'label': 'Reportes', 'icon': 'bi-file-text'},
            ],
            'Sistema': [
                {'url': '/settings/', 'label': 'Configuración', 'icon': 'bi-gear'},
            ],
        },
    }
    return menu_sections.get(role, {})
