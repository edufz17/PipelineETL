from datetime import date
from typing import Optional
import pandas as pd

from energy_etl.extract import extract_data
from energy_etl.transform import transform_data


def run_pipeline(
        start_date: date,
        end_date: date,
        time_trunc: str = "hour",
) -> Optional[pd.DataFrame]:
    print(f"1. Extracting data from {start_date} to {end_date}...")

    raw_json = extract_data(
        start_date=start_date,
        end_date=end_date,
    )

    if not raw_json:
        print("Cancelling process: raw daw was not obtained.")
        return None

    print("Transforming data...")
    df = transform_data(raw_json=raw_json)

    if df.empty:
        print("Warning: DataFrame is empty!")
        return df

    print(f"Pipeline ran successfully! {df.size} logs have been processed!")
    return df
