from django.urls import path
from . import views

urlpatterns = [
    path('executive/', views.executive_report, name='reports-executive'),
    path('export/<str:report_type>/', views.export_report, name='reports-export'),
    path('raw/<int:source_id>/', views.raw_data, name='reports-raw-data'),
]
