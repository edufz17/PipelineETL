from typing import Optional

import pandas as pd

from energy_etl.extract import extract_data

# from energy_etl.load import load_data
from energy_etl.load import load_data
from energy_etl.params import QueryParams
from energy_etl.transform import transform_data


def run_pipeline(params: QueryParams) -> Optional[pd.DataFrame]:
    print(f"1. Extracting data from {params.start_date} to {params.end_date}...")

    raw_json = extract_data(params=params)

    if not raw_json:
        print("Cancelling process: raw data was not obtained.")
        return None

    print("Transforming data...")
    df = transform_data(raw_json=raw_json, params=params)

    if df.empty:
        print("Warning: DataFrame is empty!")
        return df

    print("Loading data into PostgreSQL...")
    loaded_rows = load_data(df)

    print(
        f"Pipeline ran successfully! {len(df)} logs processed, "
        f"{loaded_rows} rows upserted."
    )
    return df
