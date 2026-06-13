from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from core.rbac import has_module_permission


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_kpi(request):
    from apps.patients.models import Patient
    from apps.etl.models import ETLExecution
    from apps.ml.models import MLModelRegistry

    patients = Patient.objects.filter(is_valid=True)
    total = patients.count()

    kpis = {
        'total_patients': total,
        'critical_patients': patients.filter(risk_category='critical').count(),
        'hypertensive': patients.filter(systolic_bp__gte=140).count(),
        'diabetic': patients.filter(glucose__gte=126).count(),
        'smokers': patients.filter(smoking=True).count(),
        'avg_risk': round(float(patients.aggregate(Avg('risk_score'))['risk_score__avg'] or 0), 2),
    }

    if has_module_permission(request.user, 'etl'):
        etl_execs = ETLExecution.objects.all()
        kpis['etl_executions'] = etl_execs.count()
        kpis['etl_records_processed'] = etl_execs.aggregate(Sum('records_loaded'))['records_loaded__sum'] or 0
    else:
        kpis['etl_executions'] = None
        kpis['etl_records_processed'] = None

    if has_module_permission(request.user, 'ml'):
        best_model = MLModelRegistry.objects.filter(is_active=True).first()
        kpis['model_accuracy'] = best_model.accuracy if best_model else None
        kpis['model_f1'] = best_model.f1_score if best_model else None
    else:
        kpis['model_accuracy'] = None
        kpis['model_f1'] = None

    if has_module_permission(request.user, 'patients'):
        kpis['active_alerts'] = patients.filter(alerts__is_active=True).count()
    else:
        kpis['active_alerts'] = None

    return Response({'success': True, 'data': kpis})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_charts(request):
    from apps.patients.models import Patient

    patients = Patient.objects.filter(is_valid=True)

    risk_dist = list(
        patients.values('risk_category')
        .annotate(count=Count('id'))
        .order_by('risk_category')
    )

    gender_dist = list(
        patients.values('gender')
        .annotate(count=Count('id'))
    )

    age_groups = []
    ranges = [(0, 18, '0-18'), (19, 30, '19-30'), (31, 45, '31-45'),
              (46, 60, '46-60'), (61, 80, '61-80'), (81, 120, '80+')]
    for lo, hi, label in ranges:
        c = patients.filter(age__gte=lo, age__lte=hi).count()
        age_groups.append({'group': label, 'count': c})

    bmi_dist = list(
        patients.values('bmi_category')
        .annotate(count=Count('id'))
    )

    diag_dist = list(
        patients.values('diagnosis')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    return Response({
        'success': True,
        'data': {
            'risk_distribution': risk_dist,
            'gender_distribution': gender_dist,
            'age_distribution': age_groups,
            'bmi_distribution': bmi_dist,
            'diagnosis_distribution': diag_dist,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_alerts(request):
    from apps.patients.models import ClinicalAlert

    alerts = ClinicalAlert.objects.filter(is_active=True).select_related('patient')

    critical = alerts.filter(severity='critical').count()
    warnings = alerts.filter(severity='warning').count()
    info = alerts.filter(severity='info').count()

    recent = alerts.order_by('-created_at')[:20]
    recent_data = [
        {
            'id': a.id,
            'patient': f"{a.patient.first_name} {a.patient.last_name}",
            'patient_id': a.patient.patient_id,
            'alert_type': a.alert_type,
            'severity': a.severity,
            'description': a.description,
            'created_at': a.created_at.isoformat(),
        }
        for a in recent
    ]

    return Response({
        'success': True,
        'data': {
            'total': alerts.count(),
            'critical': critical,
            'warnings': warnings,
            'info': info,
            'recent': recent_data,
        }
    })


def _dashboard_view(template_name, required_perm):
    def view_fn(request):
        user = request.user
        if not user.is_authenticated:
            token = request.COOKIES.get('access_token', '')
            if token:
                try:
                    jwt_auth = JWTAuthentication()
                    validated_token = jwt_auth.get_validated_token(token)
                    user = jwt_auth.get_user(validated_token)
                except Exception:
                    pass
        if not user.is_authenticated:
            return render(request, 'dashboard/login.html')
        if not has_module_permission(user, required_perm):
            return render(request, 'dashboard/login.html', {'error': 'No tienes permiso para acceder a esta página'})
        return render(request, template_name)
    return view_fn

dashboard_page = _dashboard_view('dashboard/index.html', 'dashboard')
patients_page = _dashboard_view('dashboard/patients.html', 'patients')
etl_page = _dashboard_view('dashboard/etl.html', 'etl')
analytics_page = _dashboard_view('dashboard/analytics.html', 'analytics')
ml_page = _dashboard_view('dashboard/ml.html', 'ml')
reports_page = _dashboard_view('dashboard/reports.html', 'reports')
settings_page = _dashboard_view('dashboard/settings.html', 'settings')
