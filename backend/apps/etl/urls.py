from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sources', views.DataSourceViewSet, basename='etl-sources')
router.register(r'executions', views.ETLExecutionViewSet, basename='etl-executions')
router.register(r'logs', views.ETLLogViewSet, basename='etl-logs')
router.register(r'quality-metrics', views.DataQualityMetricViewSet, basename='etl-quality')

urlpatterns = [
    path('', include(router.urls)),
]
