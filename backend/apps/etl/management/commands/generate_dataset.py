from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Genera el dataset clínico enriquecido de ~1850 registros'

    def add_arguments(self, parser):
        parser.add_argument('--records', type=int, default=1850, help='Número de registros')
        parser.add_argument('--output', type=str, default='data/outputs', help='Directorio de salida')

    def handle(self, *args, **options):
        from core.data_generator import generate_clinical_dataset, save_dataset

        self.stdout.write(f"Generando {options['records']} registros clínicos...")
        df = generate_clinical_dataset(options['records'])
        output_dir = settings.BASE_DIR / options['output']

        xlsx_path, csv_path = save_dataset(df, str(output_dir))

        # Count distributions
        risk_dist = df['risk_category'].value_counts()
        gender_dist = df['gender'].value_counts()

        self.stdout.write(self.style.SUCCESS(f"\n✅ Dataset generado exitosamente:"))
        self.stdout.write(f"   Registros: {len(df)}")
        self.stdout.write(f"   Excel: {xlsx_path}")
        self.stdout.write(f"   CSV: {csv_path}")
        self.stdout.write(f"\n   Distribución de Riesgo:")
        for cat, count in risk_dist.items():
            self.stdout.write(f"     - {cat}: {count} ({count/len(df)*100:.1f}%)")
        self.stdout.write(f"\n   Distribución por Sexo:")
        for gen, count in gender_dist.items():
            self.stdout.write(f"     - {gen}: {count} ({count/len(df)*100:.1f}%)")
        self.stdout.write(f"\n   Estadísticas:")
        self.stdout.write(f"     - Edad promedio: {df['age'].mean():.1f}")
        self.stdout.write(f"     - IMC promedio: {df['bmi'].mean():.1f}")
        self.stdout.write(f"     - Glucosa promedio: {df['glucose'].mean():.1f}")
