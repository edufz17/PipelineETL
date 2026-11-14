import pandas as pd

from database.connection import get_connection
from database.schema import init_schema

COLUMNS = [
    "metric_id",
    "metric_type",
    "datetime_utc",
    "value",
    "unit",
    "geo_limit",
]

UPSERT_SQL = """
INSERT INTO energy_prices (
    metric_id,
    metric_type,
    datetime_utc,
    value,
    unit,
    geo_limit,
)
VALUES (
    %(metric_id)s,
    %(metric_type)s,
    %(datetime_utc)s,
    %(value)s,
    %(unit)s,
    %(geo_limit)s,
)
ON CONFLICT ON CONSTRAINT uq_energy_prices_metric_datetime
DO UPDATE SET
    metric_type = EXCLUDED.metric_type,
    value = EXCLUDED.value,
    unit = EXCLUDED.unit,
    geo_limit = EXCLUDED.geo_limit;
"""


def prepare_records(df: pd.DataFrame) -> list[dict]:
    """Cleans the DataFrame and prepares it as a list of dictionaries for SQL"""
    # 1. Renaming datetime so it matches with Postgres' table
    clean_df = df.rename(columns={"datetime": "datetime_utc"})

    # 2. Removing empty dates
    initial_rows = len(clean_df)
    clean_df = clean_df.dropna(subset=["datetime_utc", "value"])
    skipped = initial_rows - len(clean_df)
    if skipped > 0:
        print(f"Warning: skipped {skipped} incomplete rows.")

    # 3. Choosing
    clean_df = clean_df[COLUMNS]
    clean_df = clean_df.astype(object).where(pd.notna(clean_df), None)

    return clean_df.to_dict(orient="records")


def load_data(df: pd.DataFrame) -> int:
    """Guarda los registros del DataFrame en PostgreSQL y devuelve el total procesado."""
    if df.empty:
        print("No rows to load: DataFrame is empty.")
        return 0

    records = prepare_records(df)
    if not records:
        print("No valid rows to load.")
        return 0

    # Al salir del bloque 'with', psycopg hace COMMIT automático si todo va bien (o ROLLBACK si hay error)
    with get_connection() as conn:
        init_schema(conn)
        with conn.cursor() as cur:
            cur.execute("""
                        ALTER TABLE energy_prices
    DROP COLUMN IF EXISTS percentage,
    DROP COLUMN IF EXISTS updated_at;
                        """)
            cur.executemany(UPSERT_SQL, records)

    return len(records)
