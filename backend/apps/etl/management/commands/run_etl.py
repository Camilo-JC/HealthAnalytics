from django.core.management.base import BaseCommand
from django.conf import settings
from etl_engine.pipeline import ETLPipeline
from apps.etl.models import DataSource, ETLExecution
import os


class Command(BaseCommand):
    help = 'Ejecuta el pipeline ETL sobre una fuente de datos'

    def add_arguments(self, parser):
        parser.add_argument('source_id', type=int, help='ID de la fuente de datos')
        parser.add_argument('--no-async', action='store_true', help='Ejecutar en primer plano')

    def handle(self, *args, **options):
        source_id = options['source_id']
        try:
            source = DataSource.objects.get(id=source_id)
        except DataSource.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Fuente {source_id} no encontrada"))
            return

        if not source.file or not os.path.exists(source.file.path):
            self.stderr.write(self.style.ERROR(f"Archivo no encontrado para fuente {source.name}"))
            return

        execution = ETLExecution.objects.create(
            source=source,
            status='pending',
        )

        self.stdout.write(f"Iniciando ETL para: {source.name}")
        self.stdout.write(f"Tipo: {source.source_type}")
        self.stdout.write(f"Archivo: {source.original_filename}")

        pipeline = ETLPipeline(execution_id=execution.id)
        result = pipeline.run(source.file.path, source.source_type)

        if result['success']:
            self.stdout.write(self.style.SUCCESS(f"\n✅ ETL completado exitosamente:"))
            self.stdout.write(f"   Registros leídos: {result['records_read']}")
            self.stdout.write(f"   Registros procesados: {result['records_processed']}")
            self.stdout.write(f"   Registros cargados: {result['records_loaded']}")
            self.stdout.write(f"   Duplicados eliminados: {result['duplicates_removed']}")
            self.stdout.write(f"   Errores corregidos: {result['errors_corrected']}")
            self.stdout.write(f"   Valores imputados: {result['nulls_imputed']}")
            self.stdout.write(f"   Outliers tratados: {result['outliers_treated']}")
            self.stdout.write(f"   Duración: {result['duration_seconds']:.2f}s")
            self.stdout.write(f"   Calidad: {result['quality_score']:.2f}%")
        else:
            self.stderr.write(self.style.ERROR(f"\n❌ ETL fallido: {result.get('error', 'Error desconocido')}"))
