from typing import Any

import pandas as pd

from energy_etl.config import AREA, PRICE_UNIT


def transform_data(
        raw_json: dict[str, Any]
) -> pd.DataFrame:
    records = list()

    included_data = raw_json.get("included", [])
    for item in included_data:
        metric_type = item["type"]
        metric_id = item["id"]

        attributes = item.get("attributes", [])
        title = attributes.get("title", [])
        for value in attributes.get("values", []):
            records.append(
                {
                    "metric_id": metric_id,
                    "metric_type": metric_type,
                    "title": title,
                    "datetime": value.get("datetime"),
                    "price_eur_mwh": value.get("value"),
                    "percentage": value.get("percentage"),
                }
            )

    df = pd.DataFrame(records)

    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df["price_eur_mwh"] = pd.to_numeric(df["price_eur_mwh"], errors="coerce")
    df["percentage"] = pd.to_numeric(df["price_eur_mwh"], errors="coerce")

    df = df.sort_values(by=["metric_id", "datetime"]).reset_index(drop=True)
    return df
