import sys
from datetime import datetime

from energy_etl import pipeline
from energy_etl.params import QueryParams


def main():
    params = QueryParams(
        start_date=datetime(2026, 11, 4, 00, 00, 00),
        end_date=datetime.today(),
        time_trunc="hour",
    )

    try:
        df_result = pipeline.run_pipeline(params)

        if df_result is not None and not df_result.empty:
            print("Final result:")
            print(df_result.head())

    except Exception:
        print(f"CRITICAL ERROR: Pipeline failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
