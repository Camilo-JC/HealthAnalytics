import pandas as pd
import numpy as np
from django.db.models import Count, Avg, Sum, Min, Max, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.rbac import has_module_permission


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    from apps.patients.models import Patient

    patients = Patient.objects.filter(is_valid=True)
    total = patients.count()

    if total == 0:
        return Response({'success': True, 'data': {}})

    risk_dist = list(patients.values('risk_category').annotate(
        count=Count('id')
    ).order_by('risk_category'))

    gender_dist = list(patients.values('gender').annotate(
        count=Count('id')
    ))

    bmi_dist = list(patients.values('bmi_category').annotate(
        count=Count('id')
    ))

    age_stats = patients.aggregate(
        mean=Avg('age'), min=Min('age'), max=Max('age')
    )

    vitals_avg = patients.aggregate(
        avg_bmi=Avg('bmi'),
        avg_systolic=Avg('systolic_bp'),
        avg_diastolic=Avg('diastolic_bp'),
        avg_heart_rate=Avg('heart_rate'),
        avg_glucose=Avg('glucose'),
        avg_cholesterol=Avg('cholesterol'),
        avg_oxygen=Avg('oxygen_saturation'),
    )

    top_diagnoses = list(
        patients.values('diagnosis')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    critical = patients.filter(risk_category='critical').count()
    high_risk = patients.filter(risk_category='high').count()
    hypertensive = patients.filter(systolic_bp__gte=140).count()
    diabetic = patients.filter(glucose__gte=126).count()
    smokers = patients.filter(smoking=True).count()
    obese = patients.filter(bmi__gte=30).count()

    return Response({
        'success': True,
        'data': {
            'total_patients': total,
            'risk_distribution': risk_dist,
            'gender_distribution': gender_dist,
            'bmi_distribution': bmi_dist,
            'age_stats': age_stats,
            'vitals_averages': {k: round(float(v), 2) if v else 0 for k, v in vitals_avg.items()},
            'top_diagnoses': top_diagnoses,
            'critical_patients': critical,
            'high_risk_patients': high_risk,
            'hypertensive': hypertensive,
            'diabetic': diabetic,
            'smokers': smokers,
            'obese': obese,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def correlation_analysis(request):
    from apps.patients.models import Patient

    patients = Patient.objects.filter(is_valid=True)
    df = pd.DataFrame(list(patients.values(
        'age', 'bmi', 'systolic_bp', 'diastolic_bp',
        'heart_rate', 'glucose', 'cholesterol', 'oxygen_saturation',
        'smoking', 'physical_activity', 'family_history', 'alcohol_consumption',
        'risk_score'
    )))

    if df.empty:
        return Response({'success': True, 'data': {}})

    for col in ['smoking', 'physical_activity', 'family_history', 'alcohol_consumption']:
        if col in df.columns:
            df[col] = df[col].astype(int)

    corr = df.corr().round(3)
    corr_matrix = {
        str(col): {
            str(idx): (float(val) if not pd.isna(val) else None)
            for idx, val in row.items()
        }
        for col, row in corr.iterrows()
    }

    return Response({'success': True, 'data': corr_matrix})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trend_analysis(request):
    from apps.patients.models import Patient
    from apps.etl.models import ETLExecution

    patients = Patient.objects.filter(is_valid=True)

    age_groups = [
        {'label': '0-18', 'min': 0, 'max': 18},
        {'label': '19-30', 'min': 19, 'max': 30},
        {'label': '31-45', 'min': 31, 'max': 45},
        {'label': '46-60', 'min': 46, 'max': 60},
        {'label': '61-80', 'min': 61, 'max': 80},
        {'label': '80+', 'min': 81, 'max': 120},
    ]

    age_dist = []
    for group in age_groups:
        count = patients.filter(age__gte=group['min'], age__lte=group['max']).count()
        if count > 0:
            age_dist.append({'group': group['label'], 'count': count})

    risk_by_age = []
    for group in age_groups:
        subset = patients.filter(age__gte=group['min'], age__lte=group['max'])
        total = subset.count()
        if total > 0:
            risk_by_age.append({
                'group': group['label'],
                'total': total,
                'critical': subset.filter(risk_category='critical').count(),
                'high': subset.filter(risk_category='high').count(),
                'medium': subset.filter(risk_category='medium').count(),
                'low': subset.filter(risk_category='low').count(),
            })

    etl_trend = list(
        ETLExecution.objects
        .filter(created_at__gte=timezone.now() - timedelta(days=90))
        .extra({'date': "date(created_at)"})
        .values('date')
        .annotate(
            count=Count('id'),
            records=Sum('records_loaded'),
            avg_quality=Avg('quality_score'),
        )
        .order_by('date')
    )

    return Response({
        'success': True,
        'data': {
            'age_distribution': age_dist,
            'risk_by_age_group': risk_by_age,
            'etl_trend': [
                {
                    'date': str(e['date']),
                    'executions': e['count'],
                    'records': e['records'] or 0,
                    'quality': round(float(e['avg_quality']), 2) if e['avg_quality'] else 0,
                }
                for e in etl_trend
            ],
        }
    })
