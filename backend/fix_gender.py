import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.patients.models import Patient
from etl_engine.transformer import Transformer

patients = Patient.objects.filter(is_valid=True, first_name__isnull=False)
count = {'M_to_F': 0, 'F_to_M': 0}
for p in patients:
    inferred = Transformer._infer_gender_from_name(p.first_name)
    if inferred and p.gender != inferred:
        print(f'{p.patient_id}: {p.first_name} {p.last_name} - gender={p.gender} -> {inferred}')
        if p.gender == 'M' and inferred == 'F':
            count['M_to_F'] += 1
        else:
            count['F_to_M'] += 1
        p.gender = inferred
        p.save()

print(f'\nM -> F: {count["M_to_F"]}')
print(f'F -> M: {count["F_to_M"]}')
print(f'Total: {count["M_to_F"] + count["F_to_M"]}')
