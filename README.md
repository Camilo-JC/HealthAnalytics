<p align="center">
  <img src="https://img.shields.io/badge/Django-5.1-16a34a?style=for-the-badge&logo=django" alt="Django">
  <img src="https://img.shields.io/badge/Next.js-14-0f172a?style=for-the-badge&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/PostgreSQL-Neon-16a34a?style=for-the-badge&logo=postgresql" alt="Neon">
  <img src="https://img.shields.io/badge/Vercel-000?style=for-the-badge&logo=vercel" alt="Vercel">
</p>

<h1 align="center">HealthAnalytics IPS</h1>
<p align="center">Plataforma de Gestión, Analítica y Machine Learning para Datos Clínicos</p>
<p align="center">
  <a href="https://health-analytics-fawn.vercel.app">Frontend</a> ·
  <a href="https://health-analytics-api.vercel.app/api/docs/">API Docs</a>
</p>

---

## ¿Qué hace?

HealthAnalytics IPS es una plataforma web para el sector salud que permite cargar datos clínicos (CSV/Excel), procesarlos mediante un pipeline ETL inteligente, visualizar KPIs y tendencias en un dashboard interactivo, y predecir riesgo cardiovascular con modelos de Machine Learning.

**Flujo de operación:**
1. El usuario sube un archivo CSV/Excel con datos de pacientes
2. El pipeline ETL extrae, transforma y carga los datos automáticamente
3. Tres modelos ML (Random Forest, Regresión Logística, Árbol de Decisión) se entrenan con los datos cargados
4. El mejor modelo por F1-score queda activo para predicciones
5. El dashboard muestra KPIs, gráficos y resultados en tiempo real

### Módulos

| Módulo | Función |
|---|---|
| **Dashboard** | KPIs globales, distribuciones demográficas, mapa de calor de riesgo, tendencias ETL, estado de modelos ML |
| **ETL Sources** | Subida de archivos CSV/Excel con detección automática de encoding, separador y decimal (soporta formato latino) |
| **ETL Executions** | Historial de ejecuciones con métricas: registros leídos, cargados, fallidos, duplicados, calidad, duración |
| **Machine Learning** | Entrenamiento automático, comparativa de modelos, predicción manual con 11 variables, importancia de features, historial de predicciones |
| **Patients** | Lista y detalle de pacientes con datos demográficos, signos vitales y riesgo cardiovascular |
| **Reports** | Exportación de datos, alertas clínicas, matrices de riesgo, calidad de datos |

### Roles de usuario

| Rol | Email | Contraseña | Acceso |
|---|---|---|---|
| Administrador | `admin@gmail.com` | `Health123` | Completo (ETL, ML, pacientes, reportes, usuarios) |
| Doctor | `doctor@gmail.com` | `Health123` | Lectura: dashboard, pacientes, reportes, alertas |
| Analista | `analista@gmail.com` | `Health123` | Gestión ETL, ML, analítica avanzada |

---

## Arquitectura

```
Usuario (Browser)
      │
      ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│   Frontend          │      │   Backend           │      │   Base de Datos  │
│   Next.js 14        │─────▶│   Django 5 + DRF    │─────▶│   Neon PostgreSQL│
│   Tailwind + Recharts│     │   pandas + sklearn  │      │   Serverless     │
└─────────────────────┘      └─────────────────────┘      └──────────────────┘
       Vercel                       Vercel                       Neon.tech
```

**Enlaces de producción:**
- **Frontend:** [health-analytics-fawn.vercel.app](https://health-analytics-fawn.vercel.app)
- **Backend API:** [health-analytics-api.vercel.app](https://health-analytics-api.vercel.app)
- **Documentación Swagger:** [health-analytics-api.vercel.app/api/docs/](https://health-analytics-api.vercel.app/api/docs/)

---

## Estructura del proyecto

```
vita-clinical/
├── backend/
│   ├── config/                    # Configuración Django (settings, urls, wsgi, asgi, celery)
│   ├── apps/
│   │   ├── authentication/        #   Autenticación JWT y roles (RBAC)
│   │   ├── patients/              #   CRUD de pacientes y alertas clínicas
│   │   ├── etl/                   #   Módulo ETL (modelos, vistas, tareas)
│   │   ├── analytics/             #   KPIs, distribuciones y tendencias
│   │   ├── ml/                    #   Machine Learning (entrenamiento y predicción)
│   │   ├── dashboard/             #   Endpoints del dashboard
│   │   └── reports/               #   Reportes y exportación
│   ├── etl_engine/                # Motor ETL (extractor, transformer, loader, pipeline)
│   ├── core/                      # Middleware (auditoría, RBAC, excepciones)
│   ├── templates/                 # Templates HTML (login, dashboard interno)
│   ├── datasets/                  # Dataset clínico de ejemplo (1.800 registros)
│   ├── media/modelos_ml/          # Modelos .pkl entrenados
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                   # Páginas (App Router de Next.js)
│   │   │   ├── dashboard/         #   Dashboard principal con KPIs y gráficos
│   │   │   ├── etl/               #   ETL Sources y ETL Executions
│   │   │   ├── ml/                #   Modelos, predicción, comparativa, importancia
│   │   │   ├── patients/          #   Lista y detalle de pacientes
│   │   │   ├── reports/           #   Reportes, alertas, exportación
│   │   │   └── login/             #   Autenticación
│   │   ├── components/            # Componentes reutilizables
│   │   │   ├── layout/            #   Sidebar, Header
│   │   │   ├── ui/                #   shadcn/ui (botones, cards, tablas, etc.)
│   │   │   └── dashboard/         #   KPIs, gráficos Recharts
│   │   ├── hooks/                 # Custom hooks (useAuth)
│   │   ├── lib/                   # Cliente API y utilidades
│   │   └── types/                 # Interfaces TypeScript
│   ├── public/                    # Archivos estáticos
│   ├── package.json
│   └── tailwind.config.ts
├── database/scripts/              # Scripts SQL
│   ├── 01_schema.sql              #   Esquema completo (21 tablas)
│   └── 02_seed_data.sql           #   Datos semilla
├── docker/                        # Docker Compose + Dockerfile
├── docs/                          # Documentación técnica
├── render.yaml                    # Configuración Render cloud
├── Procfile                       # Procfile cloud deployment
├── build.sh                       # Script de build
└── runtime.txt                    # Python 3.12.7
```
