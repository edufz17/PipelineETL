from datetime import date

import requests
from .config import API_URL

valid_time_truncs = {"hour", "day", "month", "year"}


def extract_data(
    start_date: date,
    end_date: date,
    time_trunc: str = "hour",
) -> dict[str, Any]:

    if end_date < start_date:
        raise ValueError("End date can't be before starting date.")

    if time_trunc not in valid_time_truncs:
        raise ValueError(f"Time trunc not valid. Truncs available: {valid_time_truncs}")

    params = {
        "start_date": f"{start_date.isoformat()}T00:00",
        "end_date": f"{end_date.isoformat()}T23:59",
        "time_trunc": time_trunc,
    }

    try:
        response = requests.get(
            url=API_URL,
            params=params,
            timeout=(5, 30),
        )

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"An error has occurred while extracting the data. Error: {e}"
        )
    except ValueError as e:
        raise RuntimeError(
            f"The JSON receive is not valid"
        )
