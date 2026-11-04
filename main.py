import sys
import traceback
from datetime import date
from zoneinfo import ZoneInfo

import pandas as pd

from energy_etl import pipeline
from energy_etl.params import QueryParams

MADRID_TZ = ZoneInfo("Europe/Madrid")
DISPLAY_DATE_FORMAT = "%Y-%m-%d %H:%M %Z"


def configure_display() -> None:
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)


def to_madrid_time(df: pd.DataFrame) -> pd.DataFrame:
    view = df.copy()
    datetimes = view["datetime"]
    if datetimes.dt.tz is not None:
        datetimes = datetimes.dt.tz_convert(MADRID_TZ)
    view["datetime"] = datetimes.dt.strftime(DISPLAY_DATE_FORMAT)
    return view


def main():
    params = QueryParams(
        start_date=date(2026, 11, 2),
        end_date=date(2026, 11, 4),
        time_trunc="hour",
    )

    try:
        df_result = pipeline.run_pipeline(params)
        configure_display()

        if df_result is not None and not df_result.empty:
            print("Final result (Madrid time):")
            print(to_madrid_time(df_result.head(5)).to_string(index=False))
            print(to_madrid_time(df_result.tail(5)).to_string(index=False))

    except Exception as e:
        print(f"CRITICAL ERROR: Pipeline failed -> {type(e).__name__}: {e}") # Surfaces the specific error
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
