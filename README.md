# HealthAnalytics IPS - Plataforma de Analítica Clínica Inteligente

HealthAnalytics IPS es una plataforma empresarial full stack orientada al procesamiento ETL, análisis demográfico y predicción de riesgos clínicos utilizando inteligencia artificial. La solución emplea una arquitectura desacoplada para optimizar el rendimiento y la escalabilidad.

---

## 🚀 Inicio Rápido (Local)

El proyecto requiere **Python 3.12+** y **Node.js 18+** instalados en el sistema.

### 1. Configuración del Backend (Django)
1. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```
2. Crea un archivo `.env` en la raíz del proyecto basándote en el archivo `.env.example`:
   ```env
   DJANGO_SECRET_KEY=mi-clave-secreta-de-desarrollo-12345
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   # Si no configuras base de datos PostgreSQL, se usará db.sqlite3 de forma automática
   ```
3. Realiza las migraciones de base de datos:
   ```bash
   python backend/manage.py migrate
   ```
4. Inicializa la cuenta de administrador ejecutando el endpoint de configuración o ejecutando el seed:
   ```bash
   python backend/manage.py shell -c "from apps.authentication.models import User; User.objects.get_or_create(email='admin@healthcare-etl.com', defaults={'full_name': 'Administrador', 'role': 'admin', 'is_staff': True, 'is_superuser': True})[0].set_password('Admin123!')"
   ```
5. Inicia el servidor de desarrollo:
   ```bash
   python backend/manage.py runserver
   ```

### 2. Configuración del Frontend (Next.js)
1. Ve al directorio `frontend`:
   ```bash
   cd frontend
   ```
2. Instala las dependencias:
   ```bash
   npm install
   ```
3. Copia el archivo de variables de entorno:
   ```bash
   cp .env.example .env.local
   ```
   *Nota: Por defecto, apunta a `http://localhost:8000/api/v1`*.
4. Ejecuta el servidor de desarrollo:
   ```bash
   npm run dev
   ```
5. Abre [http://localhost:3000](http://localhost:3000) en tu navegador.

---

## 🐳 Despliegue con Docker (Contenerización Completa)

El proyecto incluye soporte nativo para Docker Compose, levantando la base de datos PostgreSQL, Redis, Celery (beat y workers), el backend en Django y el frontend en Next.js.

1. Asegúrate de tener Docker y Docker Compose instalados.
2. Crea el archivo `.env` en la raíz con las credenciales correspondientes.
3. Levanta la infraestructura ejecutando:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```
4. El backend estará disponible en `http://localhost:8000` y el frontend en `http://localhost:3000`.

---

## 💾 Despliegue en la Nube

### Base de Datos PostgreSQL en Neon
1. Crea un proyecto en [Neon.tech](https://neon.tech/).
2. Copia la cadena de conexión (`DATABASE_URL`).
3. En la configuración del backend (archivo `.env` de producción o variables de entorno del servidor), define:
   ```env
   DATABASE_URL=postgres://usuario:contraseña@servidor.neon.tech/healthcare_etl?sslmode=require
   ```
4. Django detectará automáticamente la URL y configurará el backend de PostgreSQL.

### Frontend en Vercel
El frontend en Next.js está optimizado para compilar en Vercel.
1. Sube tu repositorio a GitHub.
2. Importa el proyecto desde el dashboard de Vercel.
3. Elige la carpeta raíz del framework `/frontend`.
4. Agrega la variable de entorno:
   - `NEXT_PUBLIC_API_URL`: La URL pública donde se encuentra desplegado tu Backend en Django (ej. `https://mi-backend.onrender.com/api/v1`).
5. Haz clic en **Deploy**.

### Backend en Render / Railway (Dockerizado)
El backend cuenta con una configuración `render.yaml` lista para ser desplegada en Render mediante su runtime de Docker.
1. Crea un servicio web en Render conectando tu repositorio de GitHub.
2. Selecciona la configuración de Docker y define las variables de entorno especificadas en `.env.example`.
3. Render compilará el contenedor utilizando `/docker/Dockerfile` y desplegará la API.

---

## 👥 Credenciales de Prueba por Roles

El sistema tiene implementado un sistema estricto de control de accesos basado en roles (RBAC). A continuación, se detallan las cuentas semilla integradas:

| Rol | Correo Electrónico | Contraseña | Permisos Principales |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@healthcare-etl.com` | `Admin123!` | Acceso completo (CRUD de Pacientes, ML, ETL, Reportes, Usuarios). |
| **Analista** | `analyst@healthcare-etl.com` | `Analyst123!` | Ciencia de datos (ETL, ML, Dashboard). No puede alterar pacientes ni ver reportes. |
| **Médico** | `doctor@healthcare-etl.com` | `Doctor123!` | Visualización de Dashboard, Pacientes, ML y Reportes. Solo lectura. |

---

## 📂 Estructura del Proyecto

```
├── backend/                  # Código fuente del Backend (Django + DRF)
│   ├── apps/                 # Módulos de la aplicación (patients, authentication, etl, ml, etc.)
│   ├── config/               # Configuración central (urls, settings, wsgi, celery)
│   ├── core/                 # Middleware de auditoría, RBAC y excepciones centralizadas
│   └── etl_engine/           # Motor desacoplado de ETL (Extractor, Transformer, Loader)
├── frontend/                 # Código fuente del Frontend (Next.js + Tailwind + TS)
│   ├── src/app/              # Páginas y vistas (dashboard, patients, analytics, ml, reports)
│   ├── src/components/       # UI de Shadcn, Layouts y Dashboard cards
│   ├── src/hooks/            # Hooks de sesión y permisos (useAuth)
│   └── src/types/            # Tipos e interfaces de TypeScript
├── docker/                   # Archivos de contenerización Docker y Docker Compose
├── database/                 # Scripts SQL de schema y seed
├── docs/                     # Documentación técnica y modelo ER (Mermaid)
└── dataset_clinico_etl_1800_registros.xlsx # Dataset de pruebas clínicos con errores
```

Para una descripción detallada de la arquitectura, modelo ER y APIs, consulta la [Documentación Técnica](docs/technical_documentation.md).
