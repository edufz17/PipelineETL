# REE Energy Prices ETL

An end-to-end ETL pipeline that downloads real-time electricity market prices from the Spanish grid operator ([REE](https://www.ree.es/)) public API, cleans the data with pandas, and stores it in PostgreSQL.

> This is a learning project. It is intentionally small and readable, and it grows step by step as I learn more about data engineering. Feedback and suggestions are welcome.

**Languages:** [English](#english) | [Español](#español)

---

## English

### What it does

The pipeline follows the three classic ETL stages:

1. **Extract** — requests prices from the REE `apidatos` API.
2. **Transform** — turns the nested JSON into a clean pandas `DataFrame`, converts types, and works with UTC timestamps.
3. **Load** — writes the rows to PostgreSQL with an upsert, so running the pipeline again does not create duplicates.

Some useful details:

- Typed query parameters with simple validation (`QueryParams`).
- Configurable date range, time granularity, and geographic scope.
- Timezone-aware storage in UTC; Madrid time is only used for display.
- Idempotent loads based on `(metric_id, datetime_utc)`.
- Automatic table and index creation on the first run.
- PostgreSQL 17 and pgAdmin running with Docker Compose.

### Project structure

```text
PipelineETL/
├── main.py                    # Entry point: defines the date range and runs the pipeline
├── energy_etl/                # ETL stages and configuration
│   ├── __init__.py
│   ├── config.py              # API URL, geo defaults, timeout, units
│   ├── params.py              # QueryParams dataclass and request serialization
│   ├── extract.py             # HTTP request to the REE API
│   ├── transform.py           # JSON -> pandas DataFrame
│   ├── load.py                # DataFrame -> PostgreSQL upsert
│   └── pipeline.py            # Orchestrates extract, transform and load
├── database/                  # Database helpers
│   ├── __init__.py
│   ├── connection.py          # Connection using environment variables
│   └── schema.py              # SQL for the energy_prices table and index
├── docker-compose.yaml        # PostgreSQL 17 + pgAdmin
├── pyproject.toml             # Project metadata and dependencies (uv)
├── requirements.txt           # Same dependencies for pip users
├── uv.lock                    # Locked dependency versions
├── .env.example               # Environment variable template
└── README.md
```

`energy_etl/` contains the pipeline itself. `database/` groups the connection and the table definition. `main.py` is the entry point where the date range is configured.

### Requirements

- Python 3.14 (see `.python-version`)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip with a virtual environment
- Docker Engine and Docker Compose
- Internet access to `https://apidatos.ree.es`

### Quick start

```bash
# 1. Clone the repository
git clone https://github.com/edufz17/PipelineETL.git
cd PipelineETL

# 2. Create your environment file and edit the passwords
cp .env.example .env

# 3. Start PostgreSQL and pgAdmin
docker compose up -d
docker compose ps

# 4. Install dependencies (uv recommended)
uv sync
# Alternative with pip:
# python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Wait until PostgreSQL reports `healthy`. The database listens on `127.0.0.1:5432` and pgAdmin is available at `http://localhost:8081`.

#### Create the application role (first run only)

The container creates the admin user from `POSTGRES_USER`. The pipeline connects with the application user defined in `DB_USER`, so create it once:

```bash
docker compose exec postgres psql -U postgres -d ree_pipeline
```

Inside `psql`, replace the password with the one in your `.env`:

```sql
CREATE ROLE ree_etl LOGIN PASSWORD 'change_me_app';
GRANT ALL ON SCHEMA public TO ree_etl;
\q
```

If you changed `POSTGRES_USER` or `POSTGRES_DB`, use those values instead of `postgres` and `ree_pipeline`.

#### Check the connection and run the pipeline

```bash
uv run python database/connection.py
uv run main.py
```

If you activated a virtual environment with pip, `python database/connection.py` and `python main.py` also work.

The expected result is a short summary followed by the first and last rows of the loaded data, with dates shown in Madrid time.

### Usage

The date range is defined in `main.py`:

```python
params = QueryParams(
    start_date=date(2026, 11, 2),
    end_date=date(2026, 11, 4),
    time_trunc="hour",
)
```

Change those dates before running the pipeline. `QueryParams` checks that the end date is not before the start date and that `time_trunc` is one of `hour`, `day`, `month`, or `year`.

You can also use the pipeline from your own Python code:

```python
from datetime import date

from energy_etl.params import QueryParams
from energy_etl.pipeline import run_pipeline

params = QueryParams(start_date=date(2026, 11, 2), end_date=date(2026, 11, 4))
df = run_pipeline(params)
```

### Configuration

| Variable | Used by | Description |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL container | Admin user created by the container |
| `POSTGRES_PASSWORD` | PostgreSQL container | Password for the admin user |
| `POSTGRES_DB` | PostgreSQL container | Database created on first start |
| `PGADMIN_EMAIL` | pgAdmin | Login email for pgAdmin |
| `PGADMIN_PASSWORD` | pgAdmin | Login password for pgAdmin |
| `DB_HOST` | Python app | Database host (`localhost` for local development) |
| `DB_PORT` | Python app | Host port mapped to PostgreSQL (`5432` by default) |
| `DB_NAME` | Python app | Database name |
| `DB_USER` | Python app | Application role used by the pipeline |
| `DB_PASSWORD` | Python app | Password for the application role |

The API URL, geographic defaults, timeout, and price unit live in `energy_etl/config.py`.

### Data model

Rows are stored in `energy_prices`:

| Column | Type | Description |
|---|---|---|
| `id` | `BIGSERIAL` | Surrogate primary key |
| `metric_id` | `TEXT` | REE metric ID |
| `metric_type` | `TEXT` | Metric name (for example `PVPC`) |
| `datetime_utc` | `TIMESTAMPTZ` | Price period, stored in UTC |
| `value` | `NUMERIC(12,4)` | Price value |
| `unit` | `TEXT` | Price unit (`EUR/MWh`) |
| `geo_limit` | `TEXT` | Geographic scope (`peninsular`) |
| `created_at` | `TIMESTAMPTZ` | First insert timestamp |

The unique constraint `(metric_id, datetime_utc)` makes the load idempotent. On conflict, the pipeline updates `metric_type`, `value`, `unit`, and `geo_limit`.

### How the load works

`energy_etl/load.py`:

1. Renames the DataFrame column `datetime` to `datetime_utc`.
2. Drops rows with missing `datetime` or `value`, reporting how many were skipped.
3. Creates the table and index if they do not exist.
4. Runs an `INSERT ... ON CONFLICT DO UPDATE` statement for every record.
5. Returns the number of rows processed (inserted or updated).

### Useful database queries

```bash
docker compose exec postgres psql -U ree_etl -d ree_pipeline
```

```sql
-- Count rows
SELECT count(*) FROM energy_prices;

-- Latest prices
SELECT metric_id, metric_type, datetime_utc, value, unit
FROM energy_prices
ORDER BY datetime_utc DESC
LIMIT 10;

-- Check for duplicates (should return no rows)
SELECT metric_id, datetime_utc, count(*)
FROM energy_prices
GROUP BY metric_id, datetime_utc
HAVING count(*) > 1;
```

### Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `Cannot connect to the Docker daemon` | Start Docker Desktop or the Docker service. |
| `connection refused` | The container is not running or not healthy yet: `docker compose ps`, `docker compose logs postgres`. |
| `password authentication failed` | `DB_USER`/`DB_PASSWORD` do not match the role; recreate the role or update `.env`. |
| `role "ree_etl" does not exist` | Run the role creation step. |
| `Missing environment variables: ...` | `.env` is missing or incomplete; copy `.env.example` to `.env`. |
| `DataFrame is empty` | The selected date range has no data, or the API is unavailable. |
| Need a clean database | `docker compose down -v` deletes the volume, then repeat the setup steps. |

### Current limitations and next steps

- The date range is hardcoded in `main.py`; a CLI argument or environment variable would make it more flexible.
- Runs are manual: there is no scheduler yet.
- The table is created with plain SQL. For future schema changes, a migration tool would be a safer option.
- The loader still contains a small cleanup step that drops two old columns. This can be replaced by a proper migration.
- There are no automated tests yet. Good first tests: `QueryParams` validation, `transform_data` with a sample JSON, and load idempotency.
- The API may change or rate-limit requests. `extract.py` raises clear errors, but retries and backoff are not implemented.
- This is a learning project, so these improvements will be added gradually.

### Data source

Data comes from the public REE `apidatos` API:

```text
https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real
```

This project is not affiliated with REE. Respect the API terms of use and avoid unnecessary request volume.

---

## Español

### Qué hace

El pipeline sigue las tres etapas clásicas de un proceso ETL:

1. **Extraer** — solicita los precios a la API `apidatos` de REE.
2. **Transformar** — convierte el JSON anidado en un `DataFrame` de pandas, ajusta los tipos y trabaja con fechas en UTC.
3. **Cargar** — guarda las filas en PostgreSQL con un *upsert*, de modo que ejecutar el pipeline de nuevo no crea duplicados.

Algunos detalles útiles:

- Parámetros de consulta tipados y con validación sencilla (`QueryParams`).
- Rango de fechas, granularidad temporal y ámbito geográfico configurables.
- Fechas almacenadas en UTC; la hora de Madrid solo se usa para mostrar resultados.
- Cargas idempotentes basadas en `(metric_id, datetime_utc)`.
- Creación automática de la tabla y el índice en la primera ejecución.
- PostgreSQL 17 y pgAdmin funcionando con Docker Compose.

### Estructura del proyecto

```text
PipelineETL/
├── main.py                    # Punto de entrada: define el rango de fechas y ejecuta el pipeline
├── energy_etl/                # Etapas del ETL y configuración
│   ├── __init__.py
│   ├── config.py              # URL de la API, valores geográficos, timeout, unidades
│   ├── params.py              # Dataclass QueryParams y serialización de la petición
│   ├── extract.py             # Petición HTTP a la API de REE
│   ├── transform.py           # JSON -> DataFrame de pandas
│   ├── load.py                # DataFrame -> upsert en PostgreSQL
│   └── pipeline.py            # Orquesta extracción, transformación y carga
├── database/                  # Utilidades de base de datos
│   ├── __init__.py
│   ├── connection.py          # Conexión usando variables de entorno
│   └── schema.py              # SQL de la tabla energy_prices y su índice
├── docker-compose.yaml        # PostgreSQL 17 + pgAdmin
├── pyproject.toml             # Metadatos y dependencias del proyecto (uv)
├── requirements.txt           # Las mismas dependencias para usuarios de pip
├── uv.lock                    # Versiones bloqueadas de las dependencias
├── .env.example               # Plantilla de variables de entorno
└── README.md
```

`energy_etl/` contiene el pipeline. `database/` agrupa la conexión y la definición de la tabla. `main.py` es el punto de entrada donde se configura el rango de fechas.

### Requisitos

- Python 3.14 (ver `.python-version`)
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip con un entorno virtual
- Docker Engine y Docker Compose
- Acceso a Internet para llegar a `https://apidatos.ree.es`

### Inicio rápido

```bash
# 1. Clonar el repositorio
git clone https://github.com/edufz17/PipelineETL.git
cd PipelineETL

# 2. Crear el archivo de entorno y editar las contraseñas
cp .env.example .env

# 3. Arrancar PostgreSQL y pgAdmin
docker compose up -d
docker compose ps

# 4. Instalar las dependencias (uv recomendado)
uv sync
# Alternativa con pip:
# python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Espera a que PostgreSQL indique `healthy`. La base de datos escucha en `127.0.0.1:5432` y pgAdmin está disponible en `http://localhost:8081`.

#### Crear el rol de la aplicación (solo la primera vez)

El contenedor crea el usuario administrador a partir de `POSTGRES_USER`. El pipeline se conecta con el usuario de aplicación definido en `DB_USER`, así que créalo una vez:

```bash
docker compose exec postgres psql -U postgres -d ree_pipeline
```

Dentro de `psql`, sustituye la contraseña por la que tengas en `.env`:

```sql
CREATE ROLE ree_etl LOGIN PASSWORD 'change_me_app';
GRANT ALL ON SCHEMA public TO ree_etl;
\q
```

Si cambiaste `POSTGRES_USER` o `POSTGRES_DB`, usa esos valores en lugar de `postgres` y `ree_pipeline`.

#### Comprobar la conexión y ejecutar el pipeline

```bash
uv run python database/connection.py
uv run main.py
```

Si activaste un entorno virtual con pip, también funcionan `python database/connection.py` y `python main.py`.

El resultado esperado es un resumen breve seguido de las primeras y últimas filas cargadas, con las fechas en hora de Madrid.

### Uso

El rango de fechas se define en `main.py`:

```python
params = QueryParams(
    start_date=date(2026, 11, 2),
    end_date=date(2026, 11, 4),
    time_trunc="hour",
)
```

Cambia esas fechas antes de ejecutar el pipeline. `QueryParams` comprueba que la fecha final no sea anterior a la inicial y que `time_trunc` sea uno de `hour`, `day`, `month` o `year`.

También puedes usar el pipeline desde tu propio código Python:

```python
from datetime import date

from energy_etl.params import QueryParams
from energy_etl.pipeline import run_pipeline

params = QueryParams(start_date=date(2026, 11, 2), end_date=date(2026, 11, 4))
df = run_pipeline(params)
```

### Configuración

| Variable | La usa | Descripción |
|---|---|---|
| `POSTGRES_USER` | Contenedor PostgreSQL | Usuario administrador creado por el contenedor |
| `POSTGRES_PASSWORD` | Contenedor PostgreSQL | Contraseña del usuario administrador |
| `POSTGRES_DB` | Contenedor PostgreSQL | Base de datos creada en el primer arranque |
| `PGADMIN_EMAIL` | pgAdmin | Correo de acceso a pgAdmin |
| `PGADMIN_PASSWORD` | pgAdmin | Contraseña de acceso a pgAdmin |
| `DB_HOST` | Aplicación Python | Host de la base de datos (`localhost` en desarrollo) |
| `DB_PORT` | Aplicación Python | Puerto del host mapeado a PostgreSQL (`5432` por defecto) |
| `DB_NAME` | Aplicación Python | Nombre de la base de datos |
| `DB_USER` | Aplicación Python | Rol de aplicación usado por el pipeline |
| `DB_PASSWORD` | Aplicación Python | Contraseña del rol de aplicación |

La URL de la API, los valores geográficos por defecto, el timeout y la unidad de precio están en `energy_etl/config.py`.

### Modelo de datos

Las filas se guardan en `energy_prices`:

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `BIGSERIAL` | Clave primaria sustituta |
| `metric_id` | `TEXT` | ID de la métrica de REE |
| `metric_type` | `TEXT` | Nombre de la métrica (por ejemplo `PVPC`) |
| `datetime_utc` | `TIMESTAMPTZ` | Periodo del precio, almacenado en UTC |
| `value` | `NUMERIC(12,4)` | Valor del precio |
| `unit` | `TEXT` | Unidad del precio (`EUR/MWh`) |
| `geo_limit` | `TEXT` | Ámbito geográfico (`peninsular`) |
| `created_at` | `TIMESTAMPTZ` | Fecha de la primera inserción |

La restricción única `(metric_id, datetime_utc)` hace que la carga sea idempotente. En caso de conflicto, el pipeline actualiza `metric_type`, `value`, `unit` y `geo_limit`.

### Cómo funciona la carga

`energy_etl/load.py`:

1. Renombra la columna `datetime` del `DataFrame` a `datetime_utc`.
2. Descarta las filas sin `datetime` o `value`, indicando cuántas se han omitido.
3. Crea la tabla y el índice si no existen.
4. Ejecuta una sentencia `INSERT ... ON CONFLICT DO UPDATE` por cada registro.
5. Devuelve el número de filas procesadas (insertadas o actualizadas).

### Consultas útiles

```bash
docker compose exec postgres psql -U ree_etl -d ree_pipeline
```

```sql
-- Contar filas
SELECT count(*) FROM energy_prices;

-- Precios más recientes
SELECT metric_id, metric_type, datetime_utc, value, unit
FROM energy_prices
ORDER BY datetime_utc DESC
LIMIT 10;

-- Comprobar duplicados (no debería devolver filas)
SELECT metric_id, datetime_utc, count(*)
FROM energy_prices
GROUP BY metric_id, datetime_utc
HAVING count(*) > 1;
```

### Solución de problemas

| Problema | Causa probable y solución |
|---|---|
| `Cannot connect to the Docker daemon` | Arranca Docker Desktop o el servicio de Docker. |
| `connection refused` | El contenedor no está arrancado o aún no está sano: `docker compose ps`, `docker compose logs postgres`. |
| `password authentication failed` | `DB_USER`/`DB_PASSWORD` no coinciden con el rol; recrea el rol o actualiza `.env`. |
| `role "ree_etl" does not exist` | Ejecuta el paso de creación del rol. |
| `Missing environment variables: ...` | Falta `.env` o está incompleto; copia `.env.example` a `.env`. |
| `DataFrame is empty` | El rango de fechas no tiene datos o la API no está disponible. |
| Necesito una base de datos limpia | `docker compose down -v` borra el volumen; después repite los pasos de configuración. |

### Limitaciones y próximos pasos

- El rango de fechas está fijado en `main.py`; un argumento de línea de comandos o una variable de entorno lo haría más flexible.
- Las ejecuciones son manuales: todavía no hay planificador.
- La tabla se crea con SQL directo. Para futuros cambios de esquema, una herramienta de migraciones sería más segura.
- El cargador aún incluye un pequeño paso de limpieza que elimina dos columnas antiguas. Se puede sustituir por una migración.
- Todavía no hay tests automatizados. Buenas primeras pruebas: validación de `QueryParams`, `transform_data` con un JSON de ejemplo e idempotencia de la carga.
- La API puede cambiar o limitar peticiones. `extract.py` lanza errores claros, pero no hay reintentos ni *backoff*.
- Este es un proyecto de aprendizaje, así que estas mejoras se irán añadiendo poco a poco.

### Fuente de datos

Los datos provienen de la API pública `apidatos` de REE:

```text
https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real
```

Este proyecto no está afiliado a REE. Respeta las condiciones de uso de la API y evita un volumen de peticiones innecesario.
