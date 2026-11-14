import psycopg

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS energy_prices (
    id BIGSERIAL PRIMARY KEY,
    metric_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    datetime_utc TIMESTAMPTZ NOT NULL,
    value NUMERIC(12, 4) NOT NULL,
    unit TEXT NOT NULL,
    geo_limit TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_energy_prices_metric_datetime UNIQUE (metric_id, datetime_utc)
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS ix_energy_prices_datetime_utc
    ON energy_prices (datetime_utc);
"""


def init_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
        cur.execute(CREATE_INDEX_SQL)