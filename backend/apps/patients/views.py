import csv
import io
import logging
from django.http import HttpResponse
from django.db.models import Avg, Count, Min, Max
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Patient, ClinicalAlert
from .serializers import (
    PatientListSerializer, PatientDetailSerializer,
    PatientCreateSerializer, ClinicalAlertSerializer,
    PatientBulkUploadSerializer, PatientExportSerializer
)
from core.rbac import has_module_permission
from core.audit import log_audit

logger = logging.getLogger('django')


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'gender': ['exact'],
        'risk_category': ['exact', 'in'],
        'bmi_category': ['exact'],
        'smoking': ['exact'],
        'alcohol_consumption': ['exact'],
        'physical_activity': ['exact'],
        'family_history': ['exact'],
        'age': ['gte', 'lte', 'exact'],
        'bmi': ['gte', 'lte'],
        'systolic_bp': ['gte', 'lte'],
        'glucose': ['gte', 'lte'],
        'cholesterol': ['gte', 'lte'],
        'is_valid': ['exact'],
        'diagnosis_code': ['exact', 'in'],
    }
    search_fields = [
        'patient_id', 'first_name', 'last_name',
        'document_number', 'diagnosis', 'diagnosis_code'
    ]
    ordering_fields = '__all__'
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PatientCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return PatientDetailSerializer
        elif self.action == 'list':
            return PatientListSerializer
        return PatientDetailSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            permission_classes = [IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'export':
            permission_classes = [IsAuthenticated]
        elif self.action == 'bulk_upload':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)

    def perform_create(self, serializer):
        patient = serializer.save()
        log_audit(self.request.user, 'create', 'patients', resource_type='patient',
                  resource_id=patient.patient_id,
                  description=f"Paciente creado: {patient.first_name} {patient.last_name}",
                  request=self.request)

    def perform_update(self, serializer):
        old = Patient.objects.get(pk=serializer.instance.pk)
        patient = serializer.save()
        changes = []
        for field in ['risk_category', 'diagnosis', 'diagnosis_code']:
            if getattr(old, field) != getattr(patient, field):
                changes.append(f"{field}: {getattr(old, field)} -> {getattr(patient, field)}")
        if changes:
            log_audit(self.request.user, 'update', 'patients', resource_type='patient',
                      resource_id=patient.patient_id,
                      description=f"Paciente actualizado: {patient.patient_id}. {', '.join(changes)}",
                      request=self.request)

    def perform_destroy(self, instance):
        log_audit(self.request.user, 'delete', 'patients', resource_type='patient',
                  resource_id=instance.patient_id,
                  description=f"Paciente eliminado: {instance.patient_id} {instance.first_name} {instance.last_name}",
                  request=self.request)
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        if not has_module_permission(request.user, 'patients_delete'):
            return Response(
                {'success': False, 'error': 'No tienes permiso para eliminar pacientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        if not has_module_permission(request.user, 'patients_manage'):
            return Response(
                {'success': False, 'error': 'No tienes permiso para cargar pacientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = PatientBulkUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        source_name = serializer.validated_data.get('source_name', 'upload_' + file.name)

        from apps.etl.models import DataSource, ETLExecution
        source = DataSource.objects.create(
            name=source_name,
            source_type='csv' if file.name.endswith('.csv') else 'excel',
            file=file,
            original_filename=file.name,
            file_size=file.size,
            uploaded_by=request.user if request.user.is_authenticated else None,
        )
        execution = ETLExecution.objects.create(
            source=source,
            status='pending',
            executed_by=request.user if request.user.is_authenticated else None,
        )

        log_audit(request.user, 'create', 'patients', resource_type='bulk_upload',
                  resource_id=source.id,
                  description=f"Carga masiva iniciada: {file.name}",
                  request=request)

        from apps.etl.tasks import run_etl_pipeline
        task = run_etl_pipeline.delay(execution.id)
        return Response({
            'success': True,
            'message': 'Carga iniciada. Procesando datos...',
            'source_id': source.id,
            'execution_id': execution.id,
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        patient = self.get_object()
        alerts = patient.alerts.filter(is_active=True)
        serializer = ClinicalAlertSerializer(alerts, many=True)
        return Response({'success': True, 'results': serializer.data})

    @action(detail=False, methods=['get'])
    def critical(self, request):
        critical = Patient.objects.filter(risk_category='critical')
        page = self.paginate_queryset(critical)
        if page is not None:
            serializer = PatientListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PatientListSerializer(critical, many=True)
        return Response({'success': True, 'results': serializer.data})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total = Patient.objects.count()
        valid = Patient.objects.filter(is_valid=True).count()
        critical = Patient.objects.filter(risk_category='critical').count()
        high_risk = Patient.objects.filter(risk_category='high').count()
        hypertensive = Patient.objects.filter(systolic_bp__gte=140).count()
        diabetic = Patient.objects.filter(glucose__gte=126).count()
        smokers = Patient.objects.filter(smoking=True).count()
        obese = Patient.objects.filter(bmi__gte=30).count()

        return Response({
            'success': True,
            'data': {
                'total_patients': total,
                'valid_patients': valid,
                'invalid_patients': total - valid,
                'critical_patients': critical,
                'high_risk_patients': high_risk,
                'hypertensive': hypertensive,
                'diabetic': diabetic,
                'smokers': smokers,
                'obese': obese,
            }
        })

    @action(detail=False, methods=['get'])
    def by_risk(self, request):
        data = Patient.objects.values('risk_category').annotate(count=Count('id'))
        return Response({'success': True, 'results': list(data)})

    @action(detail=False, methods=['get'])
    def by_gender(self, request):
        data = Patient.objects.values('gender').annotate(count=Count('id'))
        return Response({'success': True, 'results': list(data)})

    @action(detail=False, methods=['get'])
    def by_age_group(self, request):
        data = {
            'pediatric': Patient.objects.filter(age__lt=18).count(),
            'young_adult': Patient.objects.filter(age__gte=18, age__lt=40).count(),
            'adult': Patient.objects.filter(age__gte=40, age__lt=60).count(),
            'senior': Patient.objects.filter(age__gte=60).count(),
        }
        return Response({'success': True, 'data': data})

    @action(detail=False, methods=['get'])
    def demographics(self, request):
        patients = Patient.objects.filter(is_valid=True)
        total = patients.count()
        if total == 0:
            return Response({'success': True, 'data': {}})

        avg_age = patients.aggregate(Avg('age'))['age__avg']
        avg_bmi = patients.aggregate(Avg('bmi'))['bmi__avg']
        avg_glucose = patients.aggregate(Avg('glucose'))['glucose__avg']
        avg_cholesterol = patients.aggregate(Avg('cholesterol'))['cholesterol__avg']

        return Response({
            'success': True,
            'data': {
                'avg_age': round(avg_age, 1) if avg_age else 0,
                'avg_bmi': round(avg_bmi, 2) if avg_bmi else 0,
                'avg_glucose': round(avg_glucose, 1) if avg_glucose else 0,
                'avg_cholesterol': round(avg_cholesterol, 1) if avg_cholesterol else 0,
                'total': total,
            }
        })

    @action(detail=False, methods=['post'])
    def export(self, request):
        if not has_module_permission(request.user, 'patients'):
            return Response(
                {'success': False, 'error': 'No tienes permiso para exportar pacientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = PatientExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        export_format = serializer.validated_data['format']
        filters_data = serializer.validated_data.get('filters', {})

        ALLOWED_FILTERS = {'risk_category', 'gender', 'diagnosis', 'bmi_category', 'is_valid', 'age', 'smoking'}
        filters_data = {k: v for k, v in filters_data.items() if k in ALLOWED_FILTERS}

        queryset = Patient.objects.all()
        if filters_data:
            queryset = queryset.filter(**filters_data)

        log_audit(request.user, 'export', 'patients', resource_type='export',
                  description=f"Exportación de pacientes en formato {export_format}",
                  request=request)

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="patients.csv"'
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Nombre', 'Edad', 'Sexo', 'IMC', 'Riesgo',
                'Sistólica', 'Glucosa', 'Colesterol', 'Fumador'
            ])
            for p in queryset:
                writer.writerow([
                    p.patient_id, f"{p.first_name} {p.last_name}",
                    p.age, p.gender, p.bmi, p.risk_category,
                    p.systolic_bp, p.glucose, p.cholesterol, p.smoking
                ])
            return response

        elif export_format == 'xlsx':
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = 'Patients'
            headers = ['ID', 'Nombre', 'Edad', 'Sexo', 'IMC', 'Riesgo']
            ws.append(headers)
            for p in queryset:
                ws.append([
                    p.patient_id, f"{p.first_name} {p.last_name}",
                    p.age, p.gender, float(p.bmi) if p.bmi else '',
                    p.risk_category
                ])
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="patients.xlsx"'
            wb.save(response)
            return response

        return Response({
            'success': True,
            'message': 'Formato no soportado para exportación directa'
        })


class ClinicalAlertViewSet(viewsets.ModelViewSet):
    queryset = ClinicalAlert.objects.all()
    serializer_class = ClinicalAlertSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['severity', 'is_active', 'alert_type', 'patient']
    search_fields = ['patient__first_name', 'patient__last_name', 'alert_type', 'description']

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.is_active = False
        from django.utils import timezone
        alert.resolved_at = timezone.now()
        alert.save()
        log_audit(request.user, 'update', 'patients', resource_type='alert',
                  resource_id=alert.id, description=f"Alerta resuelta: {alert.alert_type}",
                  request=request)
        return Response({'success': True, 'message': 'Alerta resuelta'})
