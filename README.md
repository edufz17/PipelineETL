# REE Energy Prices ETL

An end-to-end ETL pipeline that extracts real-time electricity market prices from the Spanish grid operator [REE](https://www.ree.es/) API, transforms the raw JSON into a clean tabular dataset, and loads it into PostgreSQL with idempotent upserts.

The project is intentionally small and readable: it demonstrates a complete, container-backed ETL flow with typed query parameters, pandas transformations, SQLAlchemy, and timezone-safe storage.

**Languages:** [English](#english) | [Español](#español)

---

## English

### Overview

The pipeline follows the classic ETL stages:

1. **Extract** — calls the REE `apidatos` endpoint for real-time market prices.
2. **Transform** — normalizes the nested JSON into a pandas `DataFrame`, converts values to numeric types, and parses timestamps to UTC.
3. **Load** — writes the rows to PostgreSQL using an `INSERT ... ON CONFLICT DO UPDATE` upsert, so running the pipeline repeatedly never creates duplicates.

### Features

- Typed query parameters with validation (`QueryParams` dataclass).
- Configurable date range, time granularity, and geographic scope.
- Timezone-aware storage: all timestamps are stored in UTC (`TIMESTAMPTZ`).
- Madrid local time conversion for terminal display only.
- Idempotent loads keyed by `(metric_id, datetime_utc)`.
- Automatic table creation on first load.
- Clear error reporting with traceback in `main.py`.
- PostgreSQL 17 running in Docker with a persistent named volume.

### Project structure

```text
PipelineETL/
├── main.py                    # Entry point: builds QueryParams and runs the pipeline
├── docker-compose.yaml        # PostgreSQL 17 service
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── energy_etl/
│   ├── config.py              # API URL, geo defaults, timeouts, units
│   ├── params.py              # QueryParams dataclass and request serialization
│   ├── extract.py             # HTTP request to the REE API
│   ├── transform.py           # JSON -> pandas DataFrame normalization
│   ├── load.py                # DataFrame -> PostgreSQL upsert
│   └── pipeline.py            # Orchestrates extract, transform, load
└── database/
    ├── connection.py          # SQLAlchemy engine and connection test
    └── schema.py              # SQLAlchemy table definition (energy_prices)
```

### Requirements

- Python 3.10+ (tested with Python 3.14)
- Docker Engine and Docker Compose
- Internet access to reach `https://apidatos.ree.es`

### Quick start

#### 1. Clone the repository

```bash
git clone https://github.com/edufz17/PipelineETL.git
cd PipelineETL
```

#### 2. Create your environment file

```bash
cp .env.example .env
```

Edit `.env` and set your own passwords:

```env
# Docker: PostgreSQL admin
PG_ADMIN_USER=postgres
PG_ADMIN_PASSWORD=change_me_admin

# Python application
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ree_pipeline
DB_USER=ree_etl
DB_PASSWORD=change_me_app
```

`.env` is ignored by Git and must never be committed.

#### 3. Start PostgreSQL

```bash
docker compose up -d
docker compose ps
```

Wait until the service reports `healthy`. The container exposes PostgreSQL on `127.0.0.1:5432`.

#### 4. Create the application role (first run only)

The Compose service creates the **admin** user from `PG_ADMIN_USER`. The pipeline connects with the **application** user from `DB_USER`, so create it once:

```bash
docker compose exec postgres psql -U postgres -d ree_pipeline
```

Inside `psql`, replace the password with the one in your `.env`:

```sql
CREATE ROLE ree_etl LOGIN PASSWORD 'change_me_app';
GRANT ALL ON SCHEMA public TO ree_etl;
\q
```

If you changed `PG_ADMIN_USER` or `DB_NAME`, use those values instead of `postgres` and `ree_pipeline`.

#### 5. Install Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 6. Verify the database connection

```bash
python database/connection.py
```

Expected output (versions may vary):

```text
Connected as 'ree_etl' to database 'ree_pipeline'
PostgreSQL 17.x ...
```

#### 7. Run the pipeline

```bash
python main.py
```

Expected output:

```text
1. Extracting data from 2026-11-02 to 2026-11-04...
Transforming data...
Loading data into PostgreSQL...
Pipeline ran successfully! 72 logs processed, 72 rows upserted.
Final result (Madrid time):
...
```

### Usage

The date range is currently configured in `main.py`:

```python
params = QueryParams(
    start_date=date(2026, 11, 2),
    end_date=date(2026, 11, 4),
    time_trunc="hour",
)
```

Change these dates before running the pipeline. `QueryParams` validates that the end date is not before the start date and that `time_trunc` is one of `hour`, `day`, `month`, or `year`.

You can also use the pipeline programmatically:

```python
from datetime import date

from energy_etl.pipeline import run_pipeline
from energy_etl.params import QueryParams

params = QueryParams(start_date=date(2026, 11, 2), end_date=date(2026, 11, 4))
df = run_pipeline(params)
```

### Configuration

| Variable | Description |
|---|---|
| `PG_ADMIN_USER` | PostgreSQL superuser created by the container |
| `PG_ADMIN_PASSWORD` | Password for the PostgreSQL superuser |
| `DB_HOST` | Database host (`localhost` for local development) |
| `DB_PORT` | Host port mapped to PostgreSQL (`5432` by default) |
| `DB_NAME` | Database name |
| `DB_USER` | Application role used by Python |
| `DB_PASSWORD` | Password for the application role |

The API URL, geographic defaults, timeout, and price unit live in `energy_etl/config.py`.

### Data model

Rows are stored in `energy_prices`:

| Column | Type | Description |
|---|---|---|
| `id` | `BIGSERIAL` | Surrogate primary key |
| `metric_id` | `TEXT` | REE metric ID (for example `1001`) |
| `metric_type` | `TEXT` | Metric name (for example `PVPC`) |
| `datetime_utc` | `TIMESTAMPTZ` | Price period, stored in UTC |
| `value` | `NUMERIC(12,4)` | Price value |
| `unit` | `TEXT` | Price unit (`EUR/MWh`) |
| `geo_limit` | `TEXT` | Geographic scope (`peninsular`) |
| `percentage` | `DOUBLE PRECISION` | Percentage reported by the API |
| `created_at` | `TIMESTAMPTZ` | First insert timestamp |
| `updated_at` | `TIMESTAMPTZ` | Last upsert timestamp |

The unique constraint `(metric_id, datetime_utc)` makes the load idempotent. On conflict, the pipeline updates `metric_type`, `value`, `unit`, `geo_limit`, `percentage`, and `updated_at`.

### How the load works

`energy_etl/load.py`:

1. Renames the DataFrame column `datetime` to `datetime_utc`.
2. Drops rows with missing `datetime` or `value`, reporting how many were skipped.
3. Creates the table and index if they do not exist.
4. Executes a single PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` statement with `RETURNING id`.
5. Returns the number of rows written (inserted or updated).

### Useful database queries

Open a shell:

```bash
docker compose exec postgres psql -U ree_etl -d ree_pipeline
```

Count rows:

```sql
SELECT count(*) FROM energy_prices;
```

Inspect the latest prices:

```sql
SELECT metric_id, metric_type, datetime_utc, value, unit, percentage
FROM energy_prices
ORDER BY datetime_utc DESC
LIMIT 10;
```

Daily average price:

```sql
SELECT date_trunc('day', datetime_utc) AS day, avg(value) AS avg_price
FROM energy_prices
GROUP BY day
ORDER BY day;
```

Check for duplicates (should always return no rows):

```sql
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
| `role "ree_etl" does not exist` | Run the role creation step in section 4. |
| `Missing environment variables: ...` | `.env` is missing or incomplete; copy `.env.example` to `.env`. |
| `DataFrame is empty` | The selected date range has no data from the API, or the API is unavailable. |
| Pipeline writes 0 rows | All rows had invalid timestamps or values; check the extract response. |
| Need a clean database | `docker compose down -v` deletes the volume, then repeat steps 3 and 4. |

### Current limitations and next steps

- The date range is hardcoded in `main.py`; a CLI argument or environment-driven range would make it more flexible.
- There is no scheduler, so runs are manual.
- The schema is created from SQLAlchemy metadata; for production use, consider Alembic migrations.
- Raw API payloads are not retained. If auditability is needed, add a `raw_api_payloads` table with `JSONB`.
- There are no automated tests yet. Useful first tests: `QueryParams` validation, `transform_data` on a fixture JSON, and an idempotency test for `load_data`.
- The API may change its response shape or rate-limit requests; `extract.py` raises clear errors, but retries/backoff are not implemented.

### Data source

Data comes from the public REE `apidatos` API:

```text
https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real
```

This project is not affiliated with REE. Respect the API terms of use and avoid unnecessary request volume.

---

## Español

### Descripción general

Pipeline ETL que extrae los precios del mercado eléctrico en tiempo real desde la API pública de [REE](https://www.ree.es/), transforma el JSON en un `DataFrame` limpio y lo carga en PostgreSQL mediante *upserts* idempotentes.

El proyecto es pequeño y legible a propósito: muestra un flujo ETL completo con PostgreSQL en Docker, parámetros tipados, transformaciones con pandas, SQLAlchemy y almacenamiento seguro de zonas horarias.

### Características

- Parámetros de consulta tipados y validados (`QueryParams`).
- Rango de fechas, granularidad temporal y ámbito geográfico configurables.
- Fechas almacenadas en UTC (`TIMESTAMPTZ`).
- Conversión a hora de Madrid solo para mostrar por terminal.
- Cargas idempotentes con clave `(metric_id, datetime_utc)`.
- Creación automática de la tabla en la primera carga.
- Errores claros con traza completa en `main.py`.
- PostgreSQL 17 en Docker con volumen persistente.

### Estructura del proyecto

```text
PipelineETL/
├── main.py                    # Punto de entrada: crea QueryParams y ejecuta el pipeline
├── docker-compose.yaml        # Servicio PostgreSQL 17
├── requirements.txt           # Dependencias de Python
├── .env.example               # Plantilla de variables de entorno
├── energy_etl/
│   ├── config.py              # URL de la API, valores geográficos, timeouts, unidades
│   ├── params.py              # Dataclass QueryParams y serialización de la petición
│   ├── extract.py             # Petición HTTP a la API de REE
│   ├── transform.py           # Normalización de JSON a DataFrame de pandas
│   ├── load.py                # Upsert del DataFrame en PostgreSQL
│   └── pipeline.py            # Orquesta extracción, transformación y carga
└── database/
    ├── connection.py          # Motor SQLAlchemy y prueba de conexión
    └── schema.py              # Definición de la tabla energy_prices
```

### Requisitos

- Python 3.10 o superior (probado con Python 3.14)
- Docker Engine y Docker Compose
- Acceso a Internet para llegar a `https://apidatos.ree.es`

### Inicio rápido

#### 1. Clonar el repositorio

```bash
git clone https://github.com/edufz17/PipelineETL.git
cd PipelineETL
```

#### 2. Crear el archivo de entorno

```bash
cp .env.example .env
```

Edita `.env` y define tus propias contraseñas:

```env
# Docker: administrador de PostgreSQL
PG_ADMIN_USER=postgres
PG_ADMIN_PASSWORD=change_me_admin

# Aplicación Python
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ree_pipeline
DB_USER=ree_etl
DB_PASSWORD=change_me_app
```

`.env` está ignorado por Git y no debe subirse al repositorio.

#### 3. Arrancar PostgreSQL

```bash
docker compose up -d
docker compose ps
```

Espera a que el servicio aparezca como `healthy`. El contenedor expone PostgreSQL en `127.0.0.1:5432`.

#### 4. Crear el rol de la aplicación (solo la primera vez)

El servicio de Compose crea el usuario **administrador** a partir de `PG_ADMIN_USER`. El pipeline se conecta con el usuario de **aplicación** definido en `DB_USER`, así que créalo una vez:

```bash
docker compose exec postgres psql -U postgres -d ree_pipeline
```

Dentro de `psql`, usa la contraseña que hayas puesto en `.env`:

```sql
CREATE ROLE ree_etl LOGIN PASSWORD 'change_me_app';
GRANT ALL ON SCHEMA public TO ree_etl;
\q
```

Si cambiaste `PG_ADMIN_USER` o `DB_NAME`, usa esos valores en lugar de `postgres` y `ree_pipeline`.

#### 5. Instalar las dependencias de Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 6. Comprobar la conexión a la base de datos

```bash
python database/connection.py
```

Salida esperada (las versiones pueden variar):

```text
Connected as 'ree_etl' to database 'ree_pipeline'
PostgreSQL 17.x ...
```

#### 7. Ejecutar el pipeline

```bash
python main.py
```

Salida esperada:

```text
1. Extracting data from 2026-11-02 to 2026-11-04...
Transforming data...
Loading data into PostgreSQL...
Pipeline ran successfully! 72 logs processed, 72 rows upserted.
Final result (Madrid time):
...
```

### Uso

El rango de fechas se configura actualmente en `main.py`:

```python
params = QueryParams(
    start_date=date(2026, 11, 2),
    end_date=date(2026, 11, 4),
    time_trunc="hour",
)
```

Cambia esas fechas antes de ejecutar. `QueryParams` valida que la fecha final no sea anterior a la inicial y que `time_trunc` sea `hour`, `day`, `month` o `year`.

También puedes usar el pipeline desde código:

```python
from datetime import date

from energy_etl.pipeline import run_pipeline
from energy_etl.params import QueryParams

params = QueryParams(start_date=date(2026, 11, 2), end_date=date(2026, 11, 4))
df = run_pipeline(params)
```

### Configuración

| Variable | Descripción |
|---|---|
| `PG_ADMIN_USER` | Superusuario de PostgreSQL creado por el contenedor |
| `PG_ADMIN_PASSWORD` | Contraseña del superusuario |
| `DB_HOST` | Host de la base de datos (`localhost` en desarrollo) |
| `DB_PORT` | Puerto del host mapeado a PostgreSQL (`5432` por defecto) |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Rol de aplicación usado por Python |
| `DB_PASSWORD` | Contraseña del rol de aplicación |

La URL de la API, los valores geográficos por defecto, el timeout y la unidad de precio están en `energy_etl/config.py`.

### Modelo de datos

Las filas se almacenan en `energy_prices`:

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | `BIGSERIAL` | Clave primaria sustituta |
| `metric_id` | `TEXT` | ID de la métrica de REE (por ejemplo `1001`) |
| `metric_type` | `TEXT` | Nombre de la métrica (por ejemplo `PVPC`) |
| `datetime_utc` | `TIMESTAMPTZ` | Periodo del precio, almacenado en UTC |
| `value` | `NUMERIC(12,4)` | Valor del precio |
| `unit` | `TEXT` | Unidad del precio (`EUR/MWh`) |
| `geo_limit` | `TEXT` | Ámbito geográfico (`peninsular`) |
| `percentage` | `DOUBLE PRECISION` | Porcentaje devuelto por la API |
| `created_at` | `TIMESTAMPTZ` | Fecha de la primera inserción |
| `updated_at` | `TIMESTAMPTZ` | Fecha del último upsert |

La restricción única `(metric_id, datetime_utc)` hace que la carga sea idempotente. En caso de conflicto, se actualizan `metric_type`, `value`, `unit`, `geo_limit`, `percentage` y `updated_at`.

### Cómo funciona la carga

`energy_etl/load.py`:

1. Renombra la columna `datetime` del DataFrame a `datetime_utc`.
2. Descarta filas sin `datetime` o `value`, indicando cuántas se omitieron.
3. Crea la tabla y el índice si no existen.
4. Ejecuta una única sentencia PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` con `RETURNING id`.
5. Devuelve el número de filas escritas (insertadas o actualizadas).

### Consultas útiles

Abrir una consola:

```bash
docker compose exec postgres psql -U ree_etl -d ree_pipeline
```

Contar filas:

```sql
SELECT count(*) FROM energy_prices;
```

Ver los precios más recientes:

```sql
SELECT metric_id, metric_type, datetime_utc, value, unit, percentage
FROM energy_prices
ORDER BY datetime_utc DESC
LIMIT 10;
```

Precio medio diario:

```sql
SELECT date_trunc('day', datetime_utc) AS day, avg(value) AS avg_price
FROM energy_prices
GROUP BY day
ORDER BY day;
```

Comprobar duplicados (no debería devolver filas):

```sql
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
| `role "ree_etl" does not exist` | Ejecuta la creación del rol de la sección 4. |
| `Missing environment variables: ...` | Falta `.env` o está incompleto; copia `.env.example` a `.env`. |
| `DataFrame is empty` | El rango de fechas no tiene datos en la API o la API no está disponible. |
| El pipeline escribe 0 filas | Todas las filas tenían fechas o valores inválidos; revisa la respuesta de extracción. |
| Necesito una base de datos limpia | `docker compose down -v` borra el volumen; después repite los pasos 3 y 4. |

### Limitaciones y próximos pasos

- El rango de fechas está fijado en `main.py`; un argumento de línea de comandos o variables de entorno lo haría más flexible.
- No hay planificador, así que las ejecuciones son manuales.
- El esquema se crea desde los metadatos de SQLAlchemy; para producción, valora migraciones con Alembic.
- No se guardan las respuestas JSON originales. Si necesitas auditoría, añade una tabla `raw_api_payloads` con `JSONB`.
- Todavía no hay tests automatizados. Buenas primeras pruebas: validación de `QueryParams`, `transform_data` con un JSON de ejemplo e idempotencia de `load_data`.
- La API puede cambiar el formato de respuesta o limitar peticiones; `extract.py` lanza errores claros, pero no hay reintentos ni *backoff*.

### Fuente de datos

Los datos provienen de la API pública `apidatos` de REE:

```text
https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real
```

Este proyecto no está afiliado a REE. Respeta las condiciones de uso de la API y evita un volumen de peticiones innecesario.
