import numpy as np
import pandas as pd
import pickle
import os
import time
import logging
from datetime import datetime
from django.conf import settings
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

logger = logging.getLogger('ml')

RISK_MAP = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
RISK_INV = {v: k for k, v in RISK_MAP.items()}

FEATURES = [
    'age', 'bmi', 'glucose', 'cholesterol',
    'systolic_bp', 'diastolic_bp', 'heart_rate',
    'smoking', 'family_history', 'physical_activity', 'alcohol_consumption',
]


class MLTrainer:
    def __init__(self):
        self.models = {}
        self.results = {}
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()

    def prepare_data(self, df):
        df = df.dropna(subset=FEATURES + ['risk_category'])
        X = df[FEATURES].copy()
        X['smoking'] = X['smoking'].astype(int)
        X['family_history'] = X['family_history'].astype(int)
        X['physical_activity'] = X['physical_activity'].astype(int)
        X['alcohol_consumption'] = X['alcohol_consumption'].astype(int)

        y = df['risk_category'].map(RISK_MAP)
        if y.isna().any():
            raise ValueError("Valores inválidos en risk_category")

        X_scaled = self.scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=settings.ML_TEST_SIZE,
            random_state=settings.ML_RANDOM_STATE, stratify=y
        )
        return X_train, X_test, y_train, y_test, X.columns.tolist()

    def train_random_forest(self, X_train, y_train):
        logger.info("Entrenando Random Forest...")
        start = time.time()

        rf = RandomForestClassifier(
            n_estimators=200, max_depth=20,
            random_state=settings.ML_RANDOM_STATE, class_weight='balanced',
            n_jobs=1
        )
        rf.fit(X_train, y_train)

        duration = time.time() - start
        logger.info(f"Random Forest entrenado en {duration:.2f}s")

        cv_scores = cross_val_score(
            rf, X_train, y_train,
            cv=3, scoring='f1_weighted'
        )

        return rf, {}, cv_scores, duration

    def train_logistic_regression(self, X_train, y_train):
        logger.info("Entrenando Regresión Logística...")
        start = time.time()

        lr = LogisticRegression(
            C=1.0, solver='lbfgs', max_iter=1000,
            random_state=settings.ML_RANDOM_STATE, class_weight='balanced'
        )
        lr.fit(X_train, y_train)

        duration = time.time() - start
        logger.info(f"Regresión Logística entrenada en {duration:.2f}s")

        cv_scores = cross_val_score(
            lr, X_train, y_train,
            cv=3, scoring='f1_weighted'
        )

        return lr, {}, cv_scores, duration

    def train_decision_tree(self, X_train, y_train):
        logger.info("Entrenando Árbol de Decisión...")
        start = time.time()

        dt = DecisionTreeClassifier(
            max_depth=15, min_samples_split=5, min_samples_leaf=2,
            criterion='gini', random_state=settings.ML_RANDOM_STATE,
            class_weight='balanced'
        )
        dt.fit(X_train, y_train)

        duration = time.time() - start
        logger.info(f"Árbol de Decisión entrenado en {duration:.2f}s")

        cv_scores = cross_val_score(
            dt, X_train, y_train,
            cv=3, scoring='f1_weighted'
        )

        return dt, {}, cv_scores, duration

    def evaluate(self, model, X_test, y_test, feature_names=None):
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

        try:
            roc = roc_auc_score(y_test, y_prob, multi_class='ovr', average='weighted')
        except Exception:
            roc = None

        cm = confusion_matrix(y_test, y_pred).tolist()
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        importance = None
        if hasattr(model, 'feature_importances_'):
            if feature_names:
                importance = {
                    name: float(imp)
                    for name, imp in zip(feature_names, model.feature_importances_)
                }
                importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        return {
            'accuracy': round(acc, 4),
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1_score': round(f1, 4),
            'roc_auc': round(roc, 4) if roc else None,
            'confusion_matrix': cm,
            'classification_report': report,
            'feature_importance': importance,
        }

    def train_all(self, df):
        X_train, X_test, y_train, y_test, feature_names = self.prepare_data(df)
        results = {}

        models_config = [
            ('random_forest', 'Random Forest', self.train_random_forest),
            ('logistic_regression', 'Regresión Logística', self.train_logistic_regression),
            ('decision_tree', 'Árbol de Decisión', self.train_decision_tree),
        ]

        for model_key, model_name, train_fn in models_config:
            model, params, cv_scores, duration = train_fn(X_train, y_train)

            eval_results = self.evaluate(model, X_test, y_test, feature_names)

            results[model_key] = {
                'model': model,
                'model_name': model_name,
                'parameters': params,
                'cv_scores': {
                    'mean': round(float(cv_scores.mean()), 4),
                    'std': round(float(cv_scores.std()), 4),
                    'scores': [round(float(s), 4) for s in cv_scores],
                },
                'duration': round(duration, 2),
                **eval_results,
                'training_records': len(X_train),
                'test_records': len(X_test),
            }

        self.results = results
        results['feature_names'] = feature_names

        model_keys = ['random_forest', 'logistic_regression', 'decision_tree']
        best_model_key = max(model_keys, key=lambda k: results[k]['f1_score'])
        results['best_model'] = best_model_key
        results['best_model_name'] = results[best_model_key]['model_name']

        return results

    def save_model(self, model_key, results):
        os.makedirs(settings.ML_MODEL_PATH, exist_ok=True)
        model_path = os.path.join(
            settings.ML_MODEL_PATH,
            f"{model_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        )
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': results[model_key]['model'],
                'scaler': self.scaler,
                'feature_names': results.get('feature_names', FEATURES),
                'metrics': {k: v for k, v in results[model_key].items() if k != 'model'},
            }, f)
        return model_path

    @staticmethod
    def predict_risk(model_obj, input_data):
        model_path = model_obj.file_path
        if not os.path.exists(model_path):
            raise FileNotFoundError(f'Archivo de modelo no encontrado: {model_path}')
        with open(model_path, 'rb') as f:
            saved = pickle.load(f)

        model = saved['model']
        scaler = saved['scaler']
        feature_names = saved.get('feature_names', FEATURES)

        df = pd.DataFrame([input_data])
        X = df[feature_names].copy()
        for col in ['smoking', 'family_history', 'physical_activity', 'alcohol_consumption']:
            if col in X.columns:
                X[col] = X[col].astype(int)

        X_scaled = scaler.transform(X)
        pred = model.predict(X_scaled)[0]
        probs = model.predict_proba(X_scaled)[0]

        return {
            'predicted_class': int(pred),
            'predicted_risk': RISK_INV.get(int(pred), 'unknown'),
            'probabilities': {
                RISK_INV.get(i, str(i)): float(probs[i])
                for i in range(len(probs))
            },
        }


class MLService:
    def __init__(self):
        self.trainer = MLTrainer()

    def train_and_register(self, user=None):
        from apps.patients.models import Patient
        from .models import MLModelRegistry

        patients = Patient.objects.filter(is_valid=True)
        df = pd.DataFrame(list(patients.values(*FEATURES, 'risk_category')))
        if len(df) < 100:
            return {'success': False, 'error': 'Datos insuficientes para entrenar'}

        results = self.trainer.train_all(df)
        registered = []

        for model_key in ['random_forest', 'logistic_regression', 'decision_tree']:
            if model_key not in results:
                continue

            model_path = self.trainer.save_model(model_key, results)
            r = results[model_key]

            version = datetime.now().strftime('%Y.%m.%d.%H%M')

            ml_model = MLModelRegistry.objects.create(
                name=r['model_name'],
                model_type=model_key,
                target_variable='risk_category',
                version=version,
                file_path=model_path,
                is_active=(model_key == results.get('best_model', 'random_forest')),
                accuracy=r['accuracy'],
                precision=r['precision'],
                recall=r['recall'],
                f1_score=r['f1_score'],
                roc_auc=r['roc_auc'],
                parameters=r['parameters'],
                feature_importance=r.get('feature_importance'),
                confusion_matrix=r['confusion_matrix'],
                classification_report=r.get('classification_report'),
                training_records=r['training_records'],
                test_records=r['test_records'],
                training_duration=r['duration'],
                trained_by=user,
            )
            registered.append(ml_model)

        return {
            'success': True,
            'models': [
                {
                    'id': m.id,
                    'name': m.name,
                    'accuracy': m.accuracy,
                    'f1_score': m.f1_score,
                    'is_best': m.is_active,
                }
                for m in registered
            ],
            'best_model': results.get('best_model_name'),
            'comparison': {
                model_key: {
                    'accuracy': r['accuracy'],
                    'precision': r['precision'],
                    'recall': r['recall'],
                    'f1_score': r['f1_score'],
                    'roc_auc': r['roc_auc'],
                }
                for model_key, r in results.items()
                if model_key in ['random_forest', 'logistic_regression', 'decision_tree']
            },
        }

    def predict(self, model_id, input_data, patient=None):
        from .models import MLModelRegistry, MLPrediction

        model_obj = None
        if model_id:
            try:
                model_obj = MLModelRegistry.objects.get(id=model_id)
            except MLModelRegistry.DoesNotExist:
                pass

        if not model_obj:
            model_obj = MLModelRegistry.objects.filter(is_active=True).first()

        if not model_obj:
            result = self.train_and_register()
            if not result.get('success'):
                return {'success': False, 'error': 'No hay modelo activo ni datos suficientes para entrenar'}
            model_obj = MLModelRegistry.objects.filter(is_active=True).first()
            if not model_obj:
                return {'success': False, 'error': 'No se pudo crear un modelo de predicción'}

        try:
            result = MLTrainer.predict_risk(model_obj, input_data)
            try:
                probabilities = result.get('probabilities', {})
                MLPrediction.objects.create(
                    model=model_obj,
                    patient=patient,
                    input_data=input_data,
                    predicted_risk=result.get('predicted_risk', 'unknown'),
                    predicted_probability=max(probabilities.values()) if probabilities else None,
                    probabilities=probabilities,
                )
            except Exception as save_e:
                logger.warning(f"No se pudo guardar el registro de predicción: {save_e}")
            return {'success': True, 'model_id': model_obj.id, **result}
        except FileNotFoundError:
            old_path = model_obj.file_path
            model_obj.is_active = False
            model_obj.save()
            new_result = self.train_and_register()
            if not new_result.get('success'):
                return {'success': False, 'error': f'Archivo del modelo no encontrado ({old_path}) y no se pudo reentrenar'}
            model_obj = MLModelRegistry.objects.filter(is_active=True).first()
            if not model_obj:
                return {'success': False, 'error': 'Archivo del modelo no encontrado'}
            result = MLTrainer.predict_risk(model_obj, input_data)
            return {'success': True, 'model_id': model_obj.id, **result}
        except Exception as e:
            return {'success': False, 'error': f'Error en predicción: {str(e)}'}
