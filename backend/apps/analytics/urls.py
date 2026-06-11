from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.dashboard_stats, name='analytics-stats'),
    path('correlations/', views.correlation_analysis, name='analytics-correlations'),
    path('trends/', views.trend_analysis, name='analytics-trends'),
]
