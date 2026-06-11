from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.PatientViewSet, basename='patients')
router.register(r'alerts', views.ClinicalAlertViewSet, basename='clinical-alerts')

urlpatterns = [
    path('', include(router.urls)),
]
