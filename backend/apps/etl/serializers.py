from rest_framework import serializers
from .models import DataSource, ETLExecution, ETLLog, DataQualityMetric


class DataSourceSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DataSource
        fields = '__all__'
        read_only_fields = ('status', 'row_count', 'file_size', 'created_at', 'updated_at')

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.full_name if obj.uploaded_by else None


class DataSourceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ('name', 'source_type', 'file', 'notes')


class ETLExecutionSerializer(serializers.ModelSerializer):
    source_name = serializers.SerializerMethodField()
    executed_by_name = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ETLExecution
        fields = '__all__'
        read_only_fields = ('created_at',)

    def get_source_name(self, obj):
        return obj.source.name if obj.source else 'N/A'

    def get_executed_by_name(self, obj):
        return obj.executed_by.full_name if obj.executed_by else 'Sistema'

    def get_duration_formatted(self, obj):
        if obj.duration_seconds:
            mins = int(obj.duration_seconds // 60)
            secs = int(obj.duration_seconds % 60)
            return f"{mins}m {secs}s"
        return 'N/A'


class ETLExecutionDetailSerializer(ETLExecutionSerializer):
    logs = serializers.SerializerMethodField()
    quality_metrics = serializers.SerializerMethodField()

    def get_logs(self, obj):
        return ETLLogSerializer(obj.logs.all()[:50], many=True).data

    def get_quality_metrics(self, obj):
        return DataQualityMetricSerializer(obj.quality_metrics.all(), many=True).data


class ETLLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ETLLog
        fields = '__all__'


class DataQualityMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataQualityMetric
        fields = '__all__'


class ETLExecuteSerializer(serializers.Serializer):
    source_id = serializers.IntegerField()
    run_async = serializers.BooleanField(default=True)


class ETLSummarySerializer(serializers.Serializer):
    total_executions = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    total_records_loaded = serializers.IntegerField()
    avg_duration = serializers.FloatField()
    avg_quality = serializers.FloatField()
