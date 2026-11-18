# Project Roadmap --- REE Energy Prices ETL

This document describes the functional expansion plan for evolving
`PipelineETL` from a standalone ingestion pipeline into a decoupled,
observable data platform.

**Languages:** [English](#english) \| [Español](#español)

------------------------------------------------------------------------

# English

## Target Architecture

The expansion preserves the current ETL core (`energy_etl/` and
`database/`) as an independent ingestion engine and introduces three
decoupled layers orchestrated through Docker Compose.

``` text
                         ┌──────────────────┐
                         │   REE Public API  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Python ETL Core │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   PostgreSQL 17  │◄──────────────┐
                         └────────┬─────────┘               │
                                  │                         │
                                  ▼                         │
                         ┌──────────────────┐      ┌────────┴─────────┐
                         │     FastAPI      │      │   Grafana OSS    │
                         │ JWT, RBAC,       │      │ BI & Pipeline    │
                         │ Pydantic         │      │ Health           │
                         └────────┬─────────┘      └──────────────────┘
                                  ▲
                                  │ HTTP / REST
                         ┌────────┴─────────┐
                         │ Streamlit Web    │
                         │ Client           │
                         └──────────────────┘
```

## Phase 1 --- Pipeline Parameterization & Execution Audit

**Goal:** Eliminate hardcoded execution parameters and introduce
operational metadata for pipeline observability.

-   **CLI execution (`main.py`):** Support `--start-date`, `--end-date`,
    and `--days` arguments through `argparse`, while preserving
    `QueryParams` validation.
-   **Audit table (`database/schema.py`):** Add an `etl_runs` table with
    the following fields:
    -   `id`
    -   `started_at`
    -   `finished_at`
    -   `duration_seconds`
    -   `rows_processed`
    -   `status`
    -   `error_message`

    The table must be created idempotently alongside `energy_prices`.
-   **Execution tracking (`energy_etl/pipeline.py`):** Instrument
    `run_pipeline()` to persist execution metrics in `etl_runs` for both
    successful and failed runs.

## Phase 2 --- Backend Service & Access Control (FastAPI)

**Goal:** Decouple data consumers from direct database access and govern
operations through a validated REST API.

-   **Read endpoints:** Provide filtered and paginated electricity-price
    series through `GET /api/v1/prices`, and execution history through
    `GET /api/v1/runs`, using Pydantic response schemas.
-   **Authentication & RBAC:** Implement the OAuth2 password flow with
    JWT tokens and two access levels:
    -   `analyst`: Read-only access to market prices and aggregated
        metrics.
    -   `admin`: Read access plus permission to trigger on-demand
        pipeline runs.
-   **On-demand ingestion:** Expose `POST /api/v1/pipeline/run`, using
    FastAPI `BackgroundTasks` to invoke `run_pipeline(params)`
    asynchronously without blocking the HTTP response.

## Phase 3 --- Interactive Web Client (Streamlit + Plotly)

**Goal:** Provide an operational web interface governed strictly by
FastAPI permissions.

-   **No direct database access:** The client communicates exclusively
    with FastAPI over HTTP and stores the JWT token in
    `st.session_state`.
-   **Market exploration:** Provide interactive date-range and
    granularity filters, dynamic time-series charts with Plotly, and
    one-click CSV exports.
-   **Admin control panel:** Provide a role-conditional view that allows
    `admin` users to launch manual ingestions for custom date ranges and
    inspect recent execution logs.

## Phase 4 --- BI & Operational Observability (Grafana OSS)

**Goal:** Continuously monitor time series for both business metrics and
ETL reliability.

-   **Containerized deployment:** Add `grafana/grafana-oss` to
    `docker-compose.yaml`, connected to PostgreSQL through a read-only
    database role.
-   **Market intelligence dashboard:** Track hourly PVPC evolution,
    daily minimum/maximum/average price spreads, and historical
    comparisons.
-   **Pipeline health dashboard:** Monitor ingestion success rates,
    execution-latency trends, and row throughput using data from
    `etl_runs`. Configure dashboards and data sources through
    version-controlled JSON/YAML provisioning files in the repository.

------------------------------------------------------------------------

# Español

## Arquitectura objetivo

La ampliación conserva el núcleo ETL actual (`energy_etl/` y
`database/`) como motor de ingesta independiente e incorpora tres capas
desacopladas desplegadas mediante Docker Compose.

``` text
                         ┌──────────────────┐
                         │   API Pública REE│
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Núcleo ETL      │
                         │  Python          │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   PostgreSQL 17  │◄──────────────┐
                         └────────┬─────────┘               │
                                  │                         │
                                  ▼                         │
                         ┌──────────────────┐      ┌────────┴─────────┐
                         │     FastAPI      │      │   Grafana OSS    │
                         │ JWT, RBAC,       │      │ BI y salud       │
                         │ validación       │      │ del pipeline     │
                         │ Pydantic         │      └──────────────────┘
                         └────────┬─────────┘
                                  ▲
                                  │ HTTP / REST
                         ┌────────┴─────────┐
                         │ Cliente web      │
                         │ Streamlit        │
                         └──────────────────┘
```

## Fase 1 --- Parametrización del pipeline y auditoría de ejecuciones

**Objetivo:** Eliminar los parámetros de ejecución definidos
directamente en el código e incorporar metadatos operativos para poder
observar y auditar cada carga.

-   **Ejecución por CLI (`main.py`):** Admitir los argumentos
    `--start-date`, `--end-date` y `--days` mediante `argparse`,
    manteniendo la validación de `QueryParams`.
-   **Tabla de auditoría (`database/schema.py`):** Añadir una tabla
    `etl_runs` con los siguientes campos:
    -   `id`
    -   `started_at`
    -   `finished_at`
    -   `duration_seconds`
    -   `rows_processed`
    -   `status`
    -   `error_message`

    La tabla debe crearse de forma idempotente junto a `energy_prices`.
-   **Registro de ejecuciones (`energy_etl/pipeline.py`):** Instrumentar
    `run_pipeline()` para persistir las métricas de ejecución en
    `etl_runs`, tanto cuando la carga finalice correctamente como cuando
    se produzca un error.

## Fase 2 --- Servicio backend y control de acceso (FastAPI)

**Objetivo:** Desacoplar a los consumidores de datos del acceso directo
a PostgreSQL y gestionar las operaciones mediante una API REST validada.

-   **Endpoints de consulta:** Exponer series de precios eléctricos
    filtradas y paginadas mediante `GET /api/v1/prices`, así como el
    historial de ejecuciones mediante `GET /api/v1/runs`, utilizando
    esquemas de respuesta definidos con Pydantic.
-   **Autenticación y RBAC:** Implementar el flujo OAuth2 de contraseña
    con tokens JWT y dos niveles de acceso:
    -   `analyst`: Acceso de solo lectura a los precios del mercado y a
        las métricas agregadas.
    -   `admin`: Acceso de lectura y permiso para iniciar ejecuciones
        del pipeline bajo demanda.
-   **Ingesta bajo demanda:** Exponer `POST /api/v1/pipeline/run`
    utilizando `BackgroundTasks` de FastAPI para ejecutar
    `run_pipeline(params)` en segundo plano, sin bloquear la respuesta
    HTTP.

## Fase 3 --- Cliente web interactivo (Streamlit + Plotly)

**Objetivo:** Ofrecer una interfaz web operativa cuyo acceso y cuyas
acciones estén gobernados por los permisos definidos en FastAPI.

-   **Sin acceso directo a la base de datos:** El cliente se comunica
    exclusivamente con FastAPI mediante HTTP y almacena el token JWT en
    `st.session_state`.
-   **Exploración del mercado:** Incorporar filtros interactivos por
    rango de fechas y granularidad, gráficas dinámicas de series
    temporales con Plotly y descarga directa de los datos consultados en
    formato CSV.
-   **Panel de administración:** Crear una vista condicionada por el rol
    del usuario que permita a los usuarios `admin` lanzar ingestas
    manuales para rangos de fechas personalizados y consultar los
    registros de las últimas ejecuciones.

## Fase 4 --- Business Intelligence y observabilidad operativa (Grafana OSS)

**Objetivo:** Monitorizar de forma continua las series temporales, tanto
desde la perspectiva del negocio como desde la fiabilidad operativa del
pipeline ETL.

-   **Despliegue en contenedor:** Integrar `grafana/grafana-oss` en
    `docker-compose.yaml`, conectado a PostgreSQL mediante un rol de
    base de datos con permisos de solo lectura.
-   **Dashboard de inteligencia de mercado:** Mostrar la evolución
    horaria del precio PVPC, la dispersión diaria (precio mínimo, máximo
    y medio) y comparativas históricas.
-   **Dashboard de salud del ETL:** Supervisar la tasa de éxito de las
    ingestas, la evolución de los tiempos de ejecución y el volumen de
    registros procesados a partir de `etl_runs`. Configurar las fuentes
    de datos y los dashboards mediante archivos de provisioning
    JSON/YAML versionados dentro del repositorio.

------------------------------------------------------------------------

## Siguientes pasos

Una vez documentada la hoja de ruta, el siguiente paso recomendado es
comenzar la implementación de la **Fase 1** sobre el proyecto actual.

1.  **Implementar la auditoría y la parametrización:** Añadir
    `etl_runs`, instrumentar `run_pipeline()` y configurar los
    argumentos de `argparse` en `main.py`.
2.  **Crear la base del backend FastAPI:** Definir la estructura inicial
    de `api/`, configurar la conexión con PostgreSQL, implementar
    autenticación JWT y desarrollar `GET /api/v1/prices`.
3.  **Preparar la presentación del proyecto:** Redactar una descripción
    breve y técnica de `PipelineETL` para utilizarla al contactar con
    empresas en procesos de selección de prácticas de Data Engineering.

### Prompts de trabajo sugeridos

**Implementar la Fase 1**

> Escríbeme el código exacto para añadir la tabla `etl_runs` en
> `database/schema.py`, instrumentar `energy_etl/pipeline.py` y añadir
> `argparse` en `main.py`. Ten en cuenta la estructura actual del
> proyecto y mantén las responsabilidades separadas.

**Crear la estructura base de FastAPI**

> Genera la estructura mínima de la carpeta `api/` con FastAPI,
> autenticación JWT básica y el endpoint `GET /api/v1/prices` conectado
> a PostgreSQL mediante `psycopg`. Adapta la implementación al esquema
> actual de la base de datos.

**Presentar el proyecto a empresas**

> Redacta un mensaje breve y directo en español para presentar mi
> repositorio `PipelineETL` al contactar con empresas para realizar
> prácticas de Data Engineering.
