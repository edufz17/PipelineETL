from typing import Any

import pandas as pd
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from database.connection import engine as default_engine
from database.schema import energy_prices, metadata

COLUMNS = (
    "metric_id",
    "metric_type",
    "datetime_utc",
    "value",
    "unit",
    "geo_limit",
    "percentage",
)


def _to_records(df: pd.DataFrame) -> tuple[list[dict[str, Any]], int]:
    prepared = df.rename(columns={"datetime": "datetime_utc"})
    records = prepared.loc[:, COLUMNS].to_dict("records")

    valid_records = [
        {
            key: (None if pd.isna(value) else value)
            for key, value in record.items()
        }
        for record in records
        if pd.notna(record["datetime_utc"]) and pd.notna(record["value"])
    ]

    return valid_records, len(records) - len(valid_records)


def load_data(
    df: pd.DataFrame,
    engine: Engine | None = None,
) -> int:
    if df.empty:
        print("No rows to load: DataFrame is empty.")
        return 0

    engine = engine or default_engine
    metadata.create_all(engine)

    records, skipped = _to_records(df)
    if skipped:
        print(f"Warning: skipped {skipped} incomplete rows.")

    if not records:
        print("No valid rows to load.")
        return 0

    statement = insert(energy_prices).values(records)
    statement = statement.on_conflict_do_update(
        constraint="uq_energy_prices_metric_datetime",
        set_={
            "metric_type": statement.excluded.metric_type,
            "value": statement.excluded.value,
            "unit": statement.excluded.unit,
            "geo_limit": statement.excluded.geo_limit,
            "percentage": statement.excluded.percentage,
            "updated_at": func.now(),
        },
    ).returning(energy_prices.c.id)

    with engine.begin() as connection:
        result = connection.execute(statement)
        return len(result.scalars().all())
