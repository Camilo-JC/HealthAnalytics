import os
import logging
from django.db.models import Avg, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import DataSource, ETLExecution, ETLLog, DataQualityMetric
from .serializers import (
    DataSourceSerializer, DataSourceCreateSerializer,
    ETLExecutionSerializer, ETLExecutionDetailSerializer,
    ETLLogSerializer, DataQualityMetricSerializer,
    ETLExecuteSerializer, ETLSummarySerializer,
)
from core.rbac import has_module_permission
from core.audit import log_audit

logger = logging.getLogger('django')


class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_type', 'status']
    search_fields = ['name', 'original_filename']

    def get_serializer_class(self):
        if self.action == 'create':
            return DataSourceCreateSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action in ['create', 'update', 'partial_update']:
            if not has_module_permission(request.user, 'etl_execute'):
                self.permission_denied(request, message='No tienes permiso para gestionar fuentes de datos')
        if self.action == 'destroy':
            if not has_module_permission(request.user, 'etl_delete'):
                self.permission_denied(request, message='No tienes permiso para eliminar fuentes de datos')

    def perform_create(self, serializer):
        try:
            file = self.request.FILES.get('file')
            extra = {'uploaded_by': self.request.user}
            if file:
                extra['original_filename'] = file.name
                extra['file_size'] = file.size
            source = serializer.save(**extra)
            log_audit(self.request.user, 'create', 'etl', resource_type='datasource',
                      resource_id=source.id, description=f"Fuente de datos creada: {source.name}",
                      request=self.request)
        except Exception as e:
            logger.exception("Error creando DataSource")
            raise

    def perform_destroy(self, instance):
        log_audit(self.request.user, 'delete', 'etl', resource_type='datasource',
                  resource_id=instance.id, description=f"Fuente de datos eliminada: {instance.name}",
                  request=self.request)
        instance.delete()

    @action(detail=False, methods=['post'])
    def upload(self, request):
        if not has_module_permission(request.user, 'etl_execute'):
            return Response(
                {'success': False, 'error': 'No tienes permiso para cargar archivos ETL'},
                status=status.HTTP_403_FORBIDDEN
            )
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'success': False, 'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        name = request.POST.get('name', file.name)
        source_type = request.POST.get('source_type', 'excel')
        source = DataSource.objects.create(
            name=name,
            source_type=source_type,
            file=file,
            original_filename=file.name,
            file_size=file.size,
        )
        log_audit(request.user, 'create', 'etl', resource_type='datasource',
                  resource_id=source.id, description=f"Fuente creada con archivo: {file.name}",
                  request=request)
        return Response({'success': True, 'message': 'Archivo cargado exitosamente', 'id': source.id})


class ETLExecutionViewSet(viewsets.ModelViewSet):
    queryset = ETLExecution.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'source']
    search_fields = ['source__name', 'error_message']
    ordering_fields = ['created_at', 'duration_seconds', 'records_loaded']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ETLExecutionDetailSerializer
        return ETLExecutionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.action == 'destroy':
            if not has_module_permission(request.user, 'etl_delete'):
                self.permission_denied(request, message='No tienes permiso para eliminar ejecuciones ETL')

    def perform_destroy(self, instance):
        log_audit(self.request.user, 'delete', 'etl', resource_type='execution',
                  resource_id=instance.id, description=f"Ejecución ETL #{instance.id} eliminada",
                  request=self.request)
        instance.delete()

    @action(detail=False, methods=['post'])
    def execute(self, request):
        if not has_module_permission(request.user, 'etl_execute'):
            return Response(
                {'success': False, 'error': 'No tienes permiso para ejecutar procesos ETL'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ETLExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source_id = serializer.validated_data['source_id']
        run_async = serializer.validated_data['run_async']

        try:
            source = DataSource.objects.get(id=source_id)
        except DataSource.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Fuente de datos no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not source.file:
            return Response(
                {'success': False, 'error': 'La fuente no tiene archivo asociado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        execution = ETLExecution.objects.create(
            source=source,
            status='pending',
            executed_by=request.user
        )

        log_audit(request.user, 'execute', 'etl', resource_type='execution',
                  resource_id=execution.id,
                  description=f"ETL iniciado: {source.name}",
                  request=request)

        if run_async:
            from .tasks import run_etl_pipeline
            task = run_etl_pipeline.delay(execution.id)
            return Response({
                'success': True,
                'message': 'ETL iniciado en segundo plano',
                'execution_id': execution.id,
                'task_id': task.id
            })
        else:
            from etl_engine.pipeline import ETLPipeline
            pipeline = ETLPipeline(execution_id=execution.id)
            result = pipeline.run(
                source.file.path,
                source.source_type,
                user=request.user,
                source_name=source.name
            )
            return Response({'success': result['success'], 'data': result})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        queryset = ETLExecution.objects.all()
        total = queryset.count()
        successful = queryset.filter(status='completed').count()
        failed = queryset.filter(status='failed').count()
        total_loaded = queryset.aggregate(Sum('records_loaded'))['records_loaded__sum'] or 0
        avg_duration = queryset.filter(duration_seconds__isnull=False).aggregate(
            Avg('duration_seconds')
        )['duration_seconds__avg'] or 0
        avg_quality = queryset.filter(quality_score__isnull=False).aggregate(
            Avg('quality_score')
        )['quality_score__avg'] or 0

        serializer = ETLSummarySerializer(data={
            'total_executions': total,
            'successful': successful,
            'failed': failed,
            'total_records_loaded': total_loaded,
            'avg_duration': round(avg_duration, 2),
            'avg_quality': round(avg_quality, 2),
        })
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def history(self, request):
        last_30 = ETLExecution.objects.all()[:30]
        serializer = self.get_serializer(last_30, many=True)
        return Response({'success': True, 'results': serializer.data})

    @action(detail=False, methods=['get'])
    def quality_trend(self, request):
        recent = ETLExecution.objects.filter(
            quality_score__isnull=False
        ).order_by('-created_at')[:20]
        data = [
            {
                'id': e.id,
                'date': e.created_at.isoformat(),
                'quality_score': e.quality_score,
                'records_loaded': e.records_loaded,
                'status': e.status,
            }
            for e in recent
        ]
        return Response({'success': True, 'results': data})


class ETLLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ETLLog.objects.all()
    serializer_class = ETLLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'phase', 'execution', 'source']
    search_fields = ['message']
    ordering = ['-created_at']

    def check_permissions(self, request):
        super().check_permissions(request)
        if not has_module_permission(request.user, 'etl'):
            self.permission_denied(request)


class DataQualityMetricViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DataQualityMetric.objects.all()
    serializer_class = DataQualityMetricSerializer
    filterset_fields = ['execution', 'passed', 'metric_name']

    def check_permissions(self, request):
        super().check_permissions(request)
        if not has_module_permission(request.user, 'etl'):
            self.permission_denied(request)
