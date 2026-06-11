from rest_framework import serializers
from .models import MLModelRegistry, MLPrediction


class MLModelRegistrySerializer(serializers.ModelSerializer):
    model_type_display = serializers.SerializerMethodField()

    class Meta:
        model = MLModelRegistry
        fields = '__all__'
        read_only_fields = ('created_at',)

    def get_model_type_display(self, obj):
        return obj.get_model_type_display()


class MLPredictionSerializer(serializers.ModelSerializer):
    model_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = MLPrediction
        fields = '__all__'

    def get_model_name(self, obj):
        return obj.model.name if obj.model else 'N/A'

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return 'N/A'


class MLPredictSerializer(serializers.Serializer):
    model_id = serializers.IntegerField(required=False)
    age = serializers.IntegerField(min_value=0, max_value=120)
    bmi = serializers.FloatField(min_value=10, max_value=60)
    glucose = serializers.FloatField(min_value=20, max_value=600)
    cholesterol = serializers.FloatField(min_value=50, max_value=500)
    systolic_bp = serializers.IntegerField(min_value=60, max_value=280)
    diastolic_bp = serializers.IntegerField(min_value=30, max_value=180)
    heart_rate = serializers.IntegerField(min_value=30, max_value=250)
    smoking = serializers.BooleanField()
    family_history = serializers.BooleanField()
    physical_activity = serializers.BooleanField()
    alcohol_consumption = serializers.BooleanField()


class MLTrainSerializer(serializers.Serializer):
    pass


class MLComparisonSerializer(serializers.Serializer):
    model = serializers.CharField()
    accuracy = serializers.FloatField()
    precision = serializers.FloatField()
    recall = serializers.FloatField()
    f1_score = serializers.FloatField()
    roc_auc = serializers.FloatField(allow_null=True)
