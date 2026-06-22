import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.patients.models import Patient

def _bp_score(sbp, dbp):
    import math
    if sbp is None:
        return 0
    sbp, dbp = float(sbp), float(dbp) if dbp else 0
    if sbp >= 180 or dbp >= 120: return 4
    if sbp >= 140 or dbp >= 90: return 3
    if sbp >= 130 or dbp >= 80: return 2
    if sbp >= 120: return 1
    return 0

def _glucose_score(glu):
    if glu is None: return 0
    glu = float(glu)
    if glu >= 300: return 4
    if glu >= 200: return 3
    if glu >= 126: return 2
    if glu >= 100: return 1
    return 0

def _bmi_score(bmi):
    if bmi is None: return 0
    bmi = float(bmi)
    if bmi >= 40: return 4
    if bmi >= 35: return 3
    if bmi >= 30: return 2
    if bmi >= 25: return 1
    return 0

def _cholesterol_score(col):
    if col is None: return 0
    col = float(col)
    if col >= 240: return 2
    if col >= 200: return 1
    return 0

def _oxygen_score(o2):
    if o2 is None: return 0
    o2 = float(o2)
    if o2 < 85: return 4
    if o2 < 90: return 3
    if o2 < 95: return 1
    return 0

def _hr_score(hr):
    if hr is None: return 0
    hr = float(hr)
    if hr > 120 or hr < 50: return 2
    if hr > 100 or hr < 60: return 1
    return 0

patients = Patient.objects.filter(is_valid=True)
updated = 0
for p in patients:
    sbp = _bp_score(p.systolic_bp, p.diastolic_bp)
    glu = _glucose_score(p.glucose)
    bmi = _bmi_score(p.bmi)
    col = _cholesterol_score(p.cholesterol)
    o2 = _oxygen_score(p.oxygen_saturation)
    hr = _hr_score(p.heart_rate)

    lifestyle = 0
    if p.smoking: lifestyle += 1
    if not p.physical_activity: lifestyle += 1
    if p.alcohol_consumption: lifestyle += 1
    if p.family_history: lifestyle += 1

    max_single = max(sbp, glu, bmi, col, o2, hr)
    total = sbp + glu + bmi + col + o2 + hr + lifestyle

    has_crisis = (p.systolic_bp and float(p.systolic_bp) >= 180) or \
                 (p.glucose and float(p.glucose) >= 300) or \
                 (p.oxygen_saturation is not None and p.oxygen_saturation < 85)

    if has_crisis or total >= 9:
        category = 'critical'
    elif max_single >= 4 or total >= 6 or (lifestyle >= 3 and max_single >= 2):
        category = 'high'
    elif max_single >= 2 or total >= 3 or lifestyle >= 3:
        category = 'medium'
    else:
        category = 'low'

    risk_score = round(min(total / 14 * 100, 100), 2)

    old_cat = p.risk_category
    if old_cat != category:
        p.risk_category = category
        p.risk_score = risk_score
        p.save()
        updated += 1
        print(f'{p.patient_id}: {p.first_name} {p.last_name} - {old_cat} -> {category} (score={risk_score} sbp={sbp} glu={glu} bmi={bmi} col={col} o2={o2} hr={hr} lifestyle={lifestyle})')

print(f'\nActualizados: {updated} pacientes')
