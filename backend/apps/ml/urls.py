from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'models', views.MLModelViewSet, basename='ml-models')
router.register(r'predictions', views.MLPredictionViewSet, basename='ml-predictions')

urlpatterns = [
    path('', include(router.urls)),
]
