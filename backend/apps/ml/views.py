import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import MLModelRegistry, MLPrediction
from .serializers import (
    MLModelRegistrySerializer, MLPredictionSerializer,
    MLPredictSerializer, MLTrainSerializer
)
from .ml_engine import MLService
from core.rbac import has_module_permission
from core.audit import log_audit

logger = logging.getLogger('ml')
ml_service = MLService()


class MLModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MLModelRegistry.objects.all()
    serializer_class = MLModelRegistrySerializer
    filterset_fields = ['model_type', 'is_active', 'target_variable']

    def check_permissions(self, request):
        super().check_permissions(request)
        if not has_module_permission(request.user, 'ml'):
            self.permission_denied(request, message='No tienes permiso para acceder a ML')

    @action(detail=False, methods=['post'])
    def train(self, request):
        if not has_module_permission(request.user, 'ml_train'):
            return Response(
                {'success': False, 'error': 'No tienes permiso para entrenar modelos'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = MLTrainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        log_audit(request.user, 'train', 'ml', resource_type='model_training',
                  description="Entrenamiento de modelos iniciado",
                  request=request)

        from .tasks import train_ml_models
        task = train_ml_models.delay()
        return Response({
            'success': True,
            'message': 'Entrenamiento de modelos iniciado',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def predict(self, request):
        if not has_module_permission(request.user, 'ml_predict'):
            return Response(
                {'success': False, 'error': 'No tienes permiso para realizar predicciones'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = MLPredictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        patient_id = serializer.validated_data.pop('patient_id', None)
        patient = None
        if patient_id:
            from apps.patients.models import Patient
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                pass

        result = ml_service.predict(
            serializer.validated_data.pop('model_id', None),
            serializer.validated_data,
            patient=patient,
        )

        log_audit(request.user, 'predict', 'ml', resource_type='prediction',
                  description="Predicción realizada",
                  request=request, success=result.get('success', False),
                  details={'input': serializer.validated_data})
        return Response(result)

    @action(detail=False, methods=['get'])
    def best(self, request):
        best = MLModelRegistry.objects.filter(is_active=True).first()
        if best:
            serializer = self.get_serializer(best)
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'error': 'No hay modelo activo'})

    @action(detail=False, methods=['get'])
    def comparison(self, request):
        models = MLModelRegistry.objects.all().order_by('-created_at')
        unique_models = {}
        for m in models:
            if m.model_type not in unique_models:
                unique_models[m.model_type] = m

        comparison = []
        for m in unique_models.values():
            comparison.append({
                'model': m.name,
                'model_type': m.model_type,
                'accuracy': m.accuracy,
                'precision': m.precision,
                'recall': m.recall,
                'f1_score': m.f1_score,
                'roc_auc': m.roc_auc,
                'version': m.version,
                'is_active': m.is_active,
                'feature_importance': m.feature_importance,
            })

        return Response({'success': True, 'results': comparison})

    @action(detail=True, methods=['get'])
    def feature_importance(self, request, pk=None):
        model = self.get_object()
        if model.feature_importance:
            return Response({'success': True, 'data': model.feature_importance})
        return Response({'success': False, 'error': 'No disponible'})


class MLPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MLPrediction.objects.all()
    serializer_class = MLPredictionSerializer
    filterset_fields = ['model', 'predicted_risk']
    ordering = ['-created_at']

    def check_permissions(self, request):
        super().check_permissions(request)
        if not has_module_permission(request.user, 'ml'):
            self.permission_denied(request, message='No tienes permiso para acceder a ML')
