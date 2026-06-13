import io
import csv
import json
import logging
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.rbac import has_module_permission
from core.audit import log_audit

logger = logging.getLogger('django')


def check_reports_access(request):
    if not has_module_permission(request.user, 'reports'):
        return False
    return True


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def executive_report(request):
    if not check_reports_access(request):
        return Response(
            {'success': False, 'error': 'No tienes permiso para acceder a reportes'},
            status=status.HTTP_403_FORBIDDEN
        )
    from apps.patients.models import Patient
    from apps.etl.models import ETLExecution

    patients = Patient.objects.filter(is_valid=True)
    total = patients.count()

    risk_counts = {
        'critical': patients.filter(risk_category='critical').count(),
        'high': patients.filter(risk_category='high').count(),
        'medium': patients.filter(risk_category='medium').count(),
        'low': patients.filter(risk_category='low').count(),
    }

    etl_execs = ETLExecution.objects.all()
    etl_total = etl_execs.count()
    etl_success = etl_execs.filter(status='completed').count()
    etl_failed = etl_execs.filter(status='failed').count()
    etl_records = etl_execs.aggregate(Sum('records_loaded'))['records_loaded__sum'] or 0
    etl_avg_quality = etl_execs.filter(quality_score__isnull=False).aggregate(
        Avg('quality_score')
    )['quality_score__avg'] or 0

    demographics = {
        'avg_age': round(float(patients.aggregate(Avg('age'))['age__avg'] or 0), 1),
        'avg_bmi': round(float(patients.aggregate(Avg('bmi'))['bmi__avg'] or 0), 1),
        'avg_glucose': round(float(patients.aggregate(Avg('glucose'))['glucose__avg'] or 0), 1),
        'avg_risk': round(float(patients.aggregate(Avg('risk_score'))['risk_score__avg'] or 0), 2),
        'hypertensive': patients.filter(systolic_bp__gte=140).count(),
        'diabetic': patients.filter(glucose__gte=126).count(),
        'smokers': patients.filter(smoking=True).count(),
        'obese': patients.filter(bmi__gte=30).count(),
    }

    top_diagnoses = list(
        patients.values('diagnosis')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    report = {
        'generated_at': timezone.now().isoformat(),
        'period': 'Últimos 90 días',
        'summary': {
            'total_patients': total,
            'total_etl_executions': etl_total,
            'successful_etl': etl_success,
            'failed_etl': etl_failed,
            'total_records_processed': etl_records,
            'average_quality_score': round(etl_avg_quality, 2),
        },
        'risk_analysis': risk_counts,
        'demographics': demographics,
        'top_diagnoses': top_diagnoses,
    }

    log_audit(request.user, 'read', 'reports', resource_type='report',
              description="Reporte ejecutivo generado",
              request=request)

    return Response({'success': True, 'data': report})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_report(request, report_type):
    if not check_reports_access(request):
        return Response(
            {'success': False, 'error': 'No tienes permiso para exportar reportes'},
            status=status.HTTP_403_FORBIDDEN
        )
    from apps.patients.models import Patient

    patients = Patient.objects.filter(is_valid=True)
    fmt = request.query_params.get('fmt', 'csv')

    if report_type == 'patients':
        data = patients.values(
            'patient_id', 'first_name', 'last_name', 'age', 'gender',
            'bmi', 'risk_category', 'systolic_bp', 'glucose',
            'cholesterol', 'smoking', 'diagnosis'
        )
        filename = 'reporte_pacientes'

    elif report_type == 'risk':
        data = patients.values(
            'patient_id', 'first_name', 'last_name', 'age', 'gender',
            'bmi', 'risk_category', 'risk_score', 'systolic_bp', 'glucose'
        ).filter(risk_category__in=['high', 'critical'])
        filename = 'reporte_riesgo'

    elif report_type == 'etl':
        from apps.etl.models import ETLExecution
        data = ETLExecution.objects.values(
            'id', 'source__name', 'status', 'records_loaded',
            'records_failed', 'quality_score', 'duration_seconds',
            'created_at'
        )
        filename = 'reporte_etl'

    else:
        return Response({'success': False, 'error': 'Tipo de reporte no válido'})

    log_audit(request.user, 'export', 'reports', resource_type='report',
              description=f"Reporte exportado: {report_type} en formato {fmt}",
              request=request)

    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        if data:
            writer = csv.DictWriter(response, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        return response

    elif fmt == 'json':
        response = HttpResponse(
            json.dumps(list(data), default=str, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
        return response

    return Response({'success': False, 'error': 'Formato no soportado'})
