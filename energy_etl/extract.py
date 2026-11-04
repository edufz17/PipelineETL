from datetime import date
from typing import Any

import requests
from energy_etl.config import API_URL, TIMEOUT, VALID_TIME_TRUNCS


def extract_data(
        start_date: date,
        end_date: date,
        time_trunc: str = "hour",
) -> dict[str, Any]:
    if end_date < start_date:
        raise ValueError("End date can't be before starting date.")

    if time_trunc not in VALID_TIME_TRUNCS:
        raise ValueError(f"Time trunc not valid. Truncs available: {VALID_TIME_TRUNCS}")

    params = {
        "start_date": f"{start_date.isoformat()}T00:00",
        "end_date": f"{end_date.isoformat()}T23:59",
        "time_trunc": time_trunc,
    }

    try:
        response = requests.get(
            url=API_URL,
            params=params,
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"An error has occurred while extracting the data: {e}"
        ) from e
    except ValueError as e:
        raise RuntimeError(
            f"The JSON receive is not valid: {e}"
        ) from e
