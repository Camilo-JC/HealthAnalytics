# 🏥 Healthcare ETL Platform

**Plataforma empresarial de gestión, análisis y Machine Learning para datos clínicos**

---

## 📋 Tabla de Contenidos
1. [Descripción General](#-descripción-general)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Stack Tecnológico](#-stack-tecnológico)
4. [Estructura del Proyecto](#-estructura-del-proyecto)
5. [Requisitos Previos](#-requisitos-previos)
6. [Instalación y Despliegue](#-instalación-y-despliegue)
7. [Modelo de Datos (ERD)](#-modelo-de-datos-erd)
8. [Pipeline ETL](#-pipeline-etl)
9. [Machine Learning](#-machine-learning)
10. [API REST](#-api-rest)
11. [Dashboard Web](#-dashboard-web)
12. [Roles y Permisos](#-roles-y-permisos)
13. [Ejecución de Pruebas](#-ejecución-de-pruebas)
14. [Manual de Usuario](#-manual-de-usuario)
15. [Despliegue en Producción](#-despliegue-en-producción)
16. [Licencia](#-licencia)

---

## 📌 Descripción General

Healthcare ETL Platform es una solución integral para la gestión, procesamiento, análisis y modelado predictivo de datos clínicos. La plataforma implementa un pipeline ETL completo (Extract, Transform, Load) sobre datasets clínicos, con capacidades avanzadas de analítica y Machine Learning para predicción de riesgo de enfermedades.

### Características Principales

- **Motor ETL Completo**: Extracción desde Excel/CSV, transformación inteligente (limpieza, imputación, normalización, cálculo de IMC y riesgo) y carga en PostgreSQL
- **Machine Learning**: Random Forest, Regresión Logística y Árbol de Decisión con optimización de hiperparámetros
- **Dashboard Interactivo**: KPIs en tiempo real, gráficas avanzadas (Chart.js + Plotly), tablas dinámicas
- **Autenticación JWT**: Control de acceso basado en roles (Administrador, Médico, Analista)
- **Alertas Clínicas**: Detección automática de pacientes críticos basada en reglas médicas
- **API REST Completa**: Documentación Swagger/OpenAPI integrada
- **Arquitectura Escalable**: Django + DRF + Celery + Redis + PostgreSQL + Docker

---

## 🏗 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Dashboard)                     │
│           Bootstrap 5 · Chart.js · Plotly · JS               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST (JSON)
┌──────────────────────▼──────────────────────────────────────┐
│                    Backend API (Django REST)                  │
│         JWT Auth · RBAC · DRF · Swagger/OpenAPI              │
└──────┬──────────────┬──────────────┬───────────────────────-─┘
       │              │              │
       ▼              ▼              ▼
┌──────────┐ ┌──────────────┐ ┌──────────────┐
│   ETL    │ │  Analytics   │ │     ML       │
│  Engine  │ │  Module      │ │   Engine     │
├──────────┤ ├──────────────┤ ├──────────────┤
│ Extract  │ │  Stats       │ │ RandomForest │
│ Transform│ │  Correlación │ │ LogReg       │
│ Load     │ │  Tendencias  │ │ DecisionTree │
└────┬─────┘ └──────────────┘ └──────┬───────┘
     │                                │
     └──────────────┬─────────────────┘
                    ▼
┌──────────────────────────────────────┐
│         PostgreSQL (Datos)           │
│         Redis (Cache/Queue)          │
│    Celery (Tareas Asíncronas)       │
└──────────────────────────────────────┘
```

### Principios de Diseño

- **Clean Architecture**: Separación en capas (presentación, aplicación, dominio, infraestructura)
- **Principios SOLID**: Cada módulo tiene una responsabilidad única
- **DRY (Don't Repeat Yourself)**: Lógica reutilizable en servicios y mixins
- **Patrón Repository**: Abstracción de acceso a datos
- **DTO (Data Transfer Objects)**: Serializadores específicos por caso de uso

---

## 🛠 Stack Tecnológico

| Categoría | Tecnología | Versión |
|-----------|-----------|---------|
| Backend | Python | 3.12+ |
| Framework Web | Django | 5.1 |
| API REST | Django REST Framework | 3.15 |
| Base de Datos | PostgreSQL | 16 |
| Cache/Queue | Redis | 7 |
| Task Queue | Celery | 5.4 |
| ML | Scikit-Learn | 1.6 |
| Data | Pandas, NumPy | 2.2, 1.26 |
| Frontend | Bootstrap 5 | 5.3 |
| Gráficas | Chart.js, Plotly | 4.4, 2.29 |
| Autenticación | JWT (SimpleJWT) | 5.4 |
| Documentación | drf-yasg (Swagger) | 1.21 |
| Contenedores | Docker | 24+ |
| WSGI | Gunicorn | 23 |

---

## 📁 Estructura del Proyecto

```
healthcare_etl_platform/
├── backend/
│   ├── apps/
│   │   ├── authentication/     # Usuarios, JWT, RBAC
│   │   ├── patients/           # Pacientes, Alertas Clínicas
│   │   ├── etl/                # Fuentes, Ejecuciones, Logs, Calidad
│   │   ├── analytics/          # Estadísticas, Correlaciones, Tendencias
│   │   ├── ml/                 # Modelos, Predicciones, Entrenamiento
│   │   ├── reports/            # Reportes Ejecutivos, Exportación
│   │   └── dashboard/          # KPIs, Charts, Alertas
│   ├── config/                 # Settings, URLs, WSGI, ASGI, Celery
│   ├── core/                   # Middleware, Exceptions, Pagination
│   ├── etl_engine/             # Extractor, Transformer, Loader, Pipeline
│   ├── static/                 # CSS, JS, Librerías
│   ├── templates/              # Dashboards HTML
│   ├── media/                  # Uploads de archivos
│   ├── logs/                   # Logs del sistema
│   └── manage.py
├── frontend/                   # Login HTML standalone
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.celery
│   └── docker-compose.yml
├── database/
│   └── scripts/
│       ├── 01_schema.sql       # Esquema completo
│       └── 02_seed_data.sql    # Datos iniciales
├── data/
│   ├── raw/                    # Datos sin procesar
│   ├── processed/              # Datos transformados
│   └── outputs/                # Datasets generados
├── docs/                       # Documentación
├── tests/                      # Pruebas
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📦 Requisitos Previos

- **Python** 3.12 o superior
- **PostgreSQL** 16+
- **Redis** 7+ (para Celery)
- **Node.js** 18+ (solo para desarrollo frontend)
- **Docker** 24+ y Docker Compose (opcional, recomendado)

---

## 🚀 Instalación y Despliegue

### 1. Clonar el repositorio

```bash
git clone https://github.com/your-org/healthcare-etl-platform.git
cd healthcare-etl-platform
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Opción A: Instalación Manual

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
cd backend
python manage.py migrate
python manage.py createsuperuser

# Generar dataset de prueba (~1850 registros)
python manage.py generate_dataset --records 1850

# Iniciar servidor
python manage.py runserver
```

### 4. Opción B: Despliegue con Docker (Recomendado)

```bash
# Iniciar todos los servicios
docker-compose -f docker/docker-compose.yml up -d

# Ejecutar migraciones
docker-compose -f docker/docker-compose.yml exec web python manage.py migrate

# Crear superusuario
docker-compose -f docker/docker-compose.yml exec web python manage.py createsuperuser

# Generar dataset
docker-compose -f docker/docker-compose.yml exec web python manage.py generate_dataset

# Acceder a la plataforma
# http://localhost:8000
```

### 5. Verificar instalación

```bash
# Verificar estado de los servicios
docker-compose -f docker/docker-compose.yml ps

# Ver logs
docker-compose -f docker/docker-compose.yml logs -f web
docker-compose -f docker/docker-compose.yml logs -f celery_worker
```

### Credenciales por defecto

| Rol | Email | Contraseña |
|-----|-------|-----------|
| Administrador | admin@healthcare-etl.com | Admin123! |
| Médico | doctor@healthcare-etl.com | Doctor123! |
| Analista | analyst@healthcare-etl.com | Analista123! |

---

## 📊 Modelo de Datos (ERD)

### Entidades Principales

1. **User** (authentication_user) - Usuarios del sistema con roles
2. **Patient** (patients_patient) - Datos clínicos de pacientes
3. **ClinicalAlert** (patients_clinicalalert) - Alertas médicas automáticas
4. **DataSource** (etl_datasource) - Fuentes de datos ETL
5. **ETLExecution** (etl_etlexecution) - Ejecuciones del pipeline ETL
6. **ETLLog** (etl_etllog) - Trazabilidad detallada ETL
7. **DataQualityMetric** (etl_dataqualitymetric) - Métricas de calidad
8. **MLModelRegistry** (ml_mlmodelregistry) - Modelos ML registrados
9. **MLPrediction** (ml_mlprediction) - Predicciones realizadas

### Relaciones

```
User 1──N DataSource (uploaded_by)
User 1──N ETLExecution (executed_by)
User 1──N MLModelRegistry (trained_by)
DataSource 1──N ETLExecution
DataSource 1──N ETLLog
ETLExecution 1──N ETLLog
ETLExecution 1──N DataQualityMetric
Patient 1──N ClinicalAlert
Patient 1──N MLPrediction
MLModelRegistry 1──N MLPrediction
```

---

## 🔄 Pipeline ETL

### Fase 1: Extract (Extracción)

- Soporte para archivos **Excel (.xlsx, .xls)** y **CSV**
- Lectura automática de encoding (UTF-8, Latin-1)
- Detección y mapeo inteligente de columnas
- Validación de estructura del archivo

### Fase 2: Transform (Transformación)

| Operación | Descripción |
|-----------|-------------|
| **Normalización de Columnas** | Mapeo de nombres (español/inglés) a campos estandarizados |
| **Eliminación de Duplicados** | Basado en patient_id o document_number |
| **Corrección Ortográfica** | Normalización de diagnósticos médicos |
| **Conversión de Tipos** | Casting seguro a int/float/boolean |
| **Validación de Rangos** | Verificación contra rangos clínicos (presión, glucosa, etc.) |
| **Tratamiento de Outliers** | Winsorización al percentil 1 y 99 |
| **Imputación de Nulos** | Media/Mediana para variables continuas, reglas clínicas |
| **Cálculo de IMC** | peso / altura² |
| **Clasificación IMC** | Bajo peso, Normal, Sobrepeso, Obesidad I/II/III |
| **Cálculo de Riesgo** | Score multifactorial (0-100) → Bajo/Medio/Alto/Crítico |

### Fase 3: Load (Carga)

- Inserción/Actualización en PostgreSQL
- Generación automática de alertas clínicas
- Cálculo de métricas de calidad de datos
- Trazabilidad completa en ETLLog

### Reglas de Riesgo Clínico

| Categoría | Score | Criterios Principales |
|-----------|-------|----------------------|
| **Crítico** | ≥ 50 | PAS ≥ 180, SpO2 ≤ 85, Glucosa ≥ 300 |
| **Alto** | 30-49 | PAS ≥ 160, Glucosa ≥ 200, IMC ≥ 40 |
| **Medio** | 15-29 | PAS ≥ 140, Glucosa ≥ 126, IMC ≥ 30, Tabaquismo |
| **Bajo** | < 15 | Sin factores de riesgo significativos |

---

## 🤖 Machine Learning

### Modelos Implementados

| Modelo | Tipo | Hiperparámetros Optimizados |
|--------|------|---------------------------|
| **Random Forest** 🌲 | Ensamble (Bagging) | n_estimators, max_depth, min_samples_split, min_samples_leaf |
| **Regresión Logística** 📈 | Lineal | C, solver, max_iter |
| **Árbol de Decisión** 🌳 | No paramétrico | max_depth, min_samples_split, criterion |

### Variables Predictoras (Features)

1. **Edad** - Años del paciente
2. **IMC** - Índice de Masa Corporal
3. **Glucosa** - Nivel de glucosa en sangre (mg/dL)
4. **Colesterol** - Colesterol total (mg/dL)
5. **Presión Sistólica** - PAS (mmHg)
6. **Presión Diastólica** - PAD (mmHg)
7. **Frecuencia Cardíaca** - Pulso (lpm)
8. **Tabaquismo** - Sí/No
9. **Antecedentes Familiares** - Sí/No
10. **Actividad Física** - Sí/No
11. **Consumo de Alcohol** - Sí/No

### Métricas de Evaluación

- **Accuracy**: Precisión global del modelo
- **Precision**: Proporción de verdaderos positivos
- **Recall**: Sensibilidad del modelo
- **F1-Score**: Media armónica de precisión y recall
- **ROC-AUC**: Área bajo la curva ROC
- **Cross-Validation**: Validación cruzada de 5 pliegues
- **Grid Search**: Optimización de hiperparámetros

---

## 🌐 API REST

### Endpoints Principales

#### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/` | Inicio de sesión |
| POST | `/api/v1/auth/logout/` | Cierre de sesión |
| GET | `/api/v1/auth/profile/` | Perfil del usuario |
| POST | `/api/v1/auth/change-password/` | Cambiar contraseña |
| POST | `/api/v1/auth/token/` | Obtener JWT |
| POST | `/api/v1/auth/token/refresh/` | Refrescar JWT |
| GET | `/api/v1/auth/users/` | Listar usuarios |
| POST | `/api/v1/auth/users/` | Crear usuario |

#### Pacientes
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/patients/` | Listar pacientes |
| POST | `/api/v1/patients/` | Crear paciente |
| GET | `/api/v1/patients/{id}/` | Detalle paciente |
| GET | `/api/v1/patients/stats/` | Estadísticas |
| GET | `/api/v1/patients/critical/` | Pacientes críticos |
| GET | `/api/v1/patients/by_risk/` | Distribución por riesgo |
| POST | `/api/v1/patients/export/` | Exportar pacientes |
| POST | `/api/v1/patients/bulk_upload/` | Carga masiva |

#### ETL
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/etl/sources/` | Fuentes de datos |
| POST | `/api/v1/etl/sources/` | Crear fuente |
| GET | `/api/v1/etl/executions/` | Ejecuciones ETL |
| POST | `/api/v1/etl/executions/execute/` | Ejecutar ETL |
| GET | `/api/v1/etl/executions/summary/` | Resumen ETL |
| GET | `/api/v1/etl/quality-metrics/` | Métricas de calidad |
| GET | `/api/v1/etl/logs/` | Logs ETL |

#### Machine Learning
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/ml/models/` | Listar modelos |
| POST | `/api/v1/ml/models/train/` | Entrenar modelos |
| POST | `/api/v1/ml/models/predict/` | Realizar predicción |
| GET | `/api/v1/ml/models/best/` | Mejor modelo |
| GET | `/api/v1/ml/models/comparison/` | Comparación modelos |

#### Dashboard
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/kpi/` | KPIs principales |
| GET | `/api/v1/dashboard/charts/` | Datos para gráficas |
| GET | `/api/v1/dashboard/alerts/` | Alertas activas |

#### Analytics
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/analytics/stats/` | Estadísticas generales |
| GET | `/api/v1/analytics/correlations/` | Matriz de correlación |
| GET | `/api/v1/analytics/trends/` | Tendencias temporales |

### Documentación Interactiva

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **OpenAPI JSON**: http://localhost:8000/swagger.json

---

## 🎨 Dashboard Web

### Módulos del Dashboard

1. **Dashboard Principal**: KPIs, gráficas de distribución, tabla de pacientes
2. **Gestión de Pacientes**: CRUD, filtros, búsqueda, exportación
3. **Ejecución ETL**: Upload drag-and-drop, historial, métricas de calidad
4. **Analítica Clínica**: Correlaciones, tendencias, distribución por grupos
5. **Machine Learning**: Comparación de modelos, predicción interactiva
6. **Reportes**: Reporte ejecutivo, exportación CSV/JSON
7. **Usuarios**: Gestión de usuarios y roles
8. **Configuración**: Ajustes del sistema

### Tecnologías Frontend

- **Bootstrap 5.3**: Sistema de layout responsive
- **Chart.js 4.4**: Gráficas de torta, barras, doughnut
- **Plotly 2.29**: Gráficas avanzadas interactivas
- **CSS3 Moderno**: Variables CSS, Flexbox, Grid, animaciones
- **JavaScript ES6**: Async/await, Fetch API, módulos

---

## 👥 Roles y Permisos

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **Administrador** | Acceso completo al sistema | CRUD pacientes, ETL, ML, usuarios, reportes |
| **Médico** | Acceso clínico | Ver pacientes, alertas, predicciones (solo lectura) |
| **Analista** | Acceso a datos y ML | ETL, ML, reportes, analytics |

---

## 🧪 Ejecución de Pruebas

```bash
# Tests generales
cd backend
python manage.py test

# Tests específicos
python manage.py test apps.patients
python manage.py test apps.etl
python manage.py test apps.ml

# Verificar calidad de código
pip install flake8 black
flake8 apps/
black --check apps/

# Generar dataset de prueba
python manage.py generate_dataset --records 1850
```

---

## 📖 Manual de Usuario

### Primeros Pasos

1. **Acceder a la plataforma**: http://localhost:8000
2. **Iniciar sesión** con credenciales del administrador
3. **Navegar** por el dashboard principal para ver KPIs

### Cargar Datos

1. Ir al módulo **ETL** → **Cargar Datos**
2. Arrastrar archivo Excel/CSV al área de upload
3. El sistema procesará automáticamente los datos
4. Verificar resultados en **Historial ETL**

### Ejecutar Machine Learning

1. Ir al módulo **Machine Learning**
2. Click en **Entrenar Modelos**
3. Esperar a que se completen los 3 modelos
4. Comparar resultados en la tabla de métricas

### Generar Reportes

1. Ir al módulo **Reportes**
2. Seleccionar tipo de reporte (Pacientes, Riesgo, ETL)
3. Elegir formato de exportación (CSV, JSON)
4. Descargar el archivo generado

### Interpretar Alertas

Las alertas clínicas se generan automáticamente cuando:
- **Presión Sistólica** ≥ 180 mmHg (Crítica) / ≥ 140 mmHg (Advertencia)
- **Glucosa** ≥ 300 mg/dL (Crítica) / ≥ 126 mg/dL (Advertencia)
- **Saturación O₂** ≤ 85% (Crítica) / ≤ 90% (Advertencia)
- **Frecuencia Cardíaca** ≥ 120 lpm (Taquicardia) / ≤ 50 lpm (Bradicardia)
- **IMC** ≥ 40 (Obesidad Mórbida)
- **Colesterol** ≥ 240 mg/dL (Hipercolesterolemia)

---

## 🚢 Despliegue en Producción

### Requisitos de Producción

- **4 vCPU**, **8 GB RAM** mínimo
- **PostgreSQL 16** con replicación
- **Redis 7** con persistencia
- **Nginx** como proxy inverso
- **SSL/TLS** (Let's Encrypt)
- **Monitoreo** (Prometheus + Grafana)

### Configuración de Nginx

```nginx
server {
    listen 80;
    server_name healthcare-etl.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name healthcare-etl.com;

    ssl_certificate /etc/letsencrypt/live/healthcare-etl.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/healthcare-etl.com/privkey.pem;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Variables de Entorno para Producción

```bash
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generar-clave-segura>
DJANGO_ALLOWED_HOSTS=healthcare-etl.com,api.healthcare-etl.com
DB_PASSWORD=<contraseña-segura>
REDIS_URL=redis://:password@redis:6379/0
CELERY_BROKER_URL=redis://:password@redis:6379/1
CELERY_RESULT_BACKEND=redis://:password@redis:6379/2
```

### Backup

```bash
# Backup de base de datos
pg_dump -h localhost -U postgres healthcare_etl > backup_$(date +%Y%m%d).sql

# Backup de archivos
tar -czf media_backup_$(date +%Y%m%d).tar.gz backend/media/
```

---

## 📄 Licencia

Este proyecto es propiedad intelectual confidencial. Todos los derechos reservados.

---

## 👨‍💻 Autor

Desarrollado como parte de un reto técnico de Analítica de Datos y Desarrollo Full Stack.

---

*Documentación generada: Junio 2026*
