from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from apps.dashboard import views as dashboard_views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Healthcare ETL Platform API",
        default_version='v1.0.0',
        description="""
        API REST para la plataforma Healthcare ETL.
        Gestión de pacientes, procesos ETL, analítica clínica y machine learning.
        """,
        terms_of_service="https://healthcare-etl.com/terms/",
        contact=openapi.Contact(email="admin@healthcare-etl.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/patients/', include('apps.patients.urls')),
    path('api/v1/etl/', include('apps.etl.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/ml/', include('apps.ml.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),

    # Swagger / OpenAPI
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Frontend dashboard
    path('login.html', TemplateView.as_view(template_name='dashboard/login.html'), name='login'),
    path('', dashboard_views.dashboard_page, name='dashboard'),
    path('patients/', dashboard_views.patients_page, name='dashboard-patients'),
    path('etl/', dashboard_views.etl_page, name='dashboard-etl'),
    path('analytics/', dashboard_views.analytics_page, name='dashboard-analytics'),
    path('ml/', dashboard_views.ml_page, name='dashboard-ml'),
    path('reports/', dashboard_views.reports_page, name='dashboard-reports'),
    path('settings/', dashboard_views.settings_page, name='dashboard-settings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
