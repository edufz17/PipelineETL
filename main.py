from datetime import date, datetime
from energy_etl import pipeline


def main():
    try:
        df_result = pipeline.run_pipeline(
            start_date=date.today(),
            end_date=datetime.today(),
            time_trunc="hour",
        )

        if df_result is not None and not df_result.empty:
            print("Final result:")
            print(df_result.head(5))

    except Exception as e:
        print(f"CRITICAL ERROR: Pipeline failed: {e}")
        return

    if __name__ == "__main__":
        main()
