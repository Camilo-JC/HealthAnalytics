from django.urls import path
from . import views

urlpatterns = [
    path('kpi/', views.dashboard_kpi, name='dashboard-kpi'),
    path('charts/', views.dashboard_charts, name='dashboard-charts'),
    path('alerts/', views.dashboard_alerts, name='dashboard-alerts'),
]
