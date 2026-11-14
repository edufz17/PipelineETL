from typing import Any

import pandas as pd

from energy_etl.config import PRICE_UNIT
from energy_etl.params import QueryParams


def transform_data(
        raw_json: dict[str, Any],
        params: QueryParams,
) -> pd.DataFrame:
    records = []

    included_data = raw_json.get("included", [])
    for item in included_data:
        metric_type = item.get("type")
        metric_id = item.get("id")

        attributes = item.get("attributes", {})
        for value in attributes.get("values", []):
            records.append(
                {
                    "metric_id": metric_id,
                    "metric_type": metric_type,
                    "datetime": value.get("datetime"),
                    "value": value.get("value"),
                    "unit": PRICE_UNIT,
                    "geo_limit": params.geo_limit,
                }
            )

    df = pd.DataFrame(records)

    if df.empty:
        print("Dataframe was empty. Couldn't transform any data...")
        return df

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.sort_values(by=["metric_id", "datetime"]).reset_index(drop=True)
    return df
