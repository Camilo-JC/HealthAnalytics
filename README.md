# HealthAnalytics IPS

Plataforma de analítica clínica inteligente para gestión, procesamiento y análisis predictivo de datos de pacientes.

## Funcionalidades

- **Pipeline ETL**: Carga y transformación de datos clínicos desde archivos Excel/CSV con limpieza automática, normalización y validación.
- **Dashboard interactivo**: KPIs en tiempo real, gráficos de distribución, alertas clínicas y tabla de pacientes con filtros.
- **Machine Learning**: Entrenamiento y comparación de modelos predictivos (Random Forest, Regresión Logística, Árbol de Decisión) para clasificación de riesgo.
- **Autenticación JWT**: Control de acceso basado en roles (Administrador, Médico, Analista).
- **API REST**: Documentación interactiva vía Swagger/OpenAPI.
- **Reportes**: Exportación ejecutiva con resúmenes y gráficos.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | Next.js, TypeScript, Tailwind CSS, Recharts |
| Backend | Django, Django REST Framework, Celery |
| Base de datos | PostgreSQL |
| ML | Scikit-Learn, Pandas, NumPy |
| Infraestructura | Docker, Gunicorn, Redis |

## Requisitos

- Python 3.12+
- PostgreSQL 16+
- Node.js 18+
- Docker (opcional)

## Inicio rápido

```bash
# Backend
cd backend
pip install -r ../requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

## Despliegue

El proyecto está dockerizado. Ver `docker/docker-compose.yml` para el entorno completo.

Frontend desplegable en Vercel. Backend desplegable en servicios compatibles con Docker (Render, Railway, etc.).

## Licencia

Todos los derechos reservados.
