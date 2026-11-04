from typing import Any

import requests

from energy_etl.config import API_URL, TIMEOUT
from energy_etl.params import QueryParams


def extract_data(params: QueryParams) -> dict[str, Any]:
    try:
        response = requests.get(
            url=API_URL,
            params=params.to_request_params(),
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.JSONDecodeError as e:
        raise RuntimeError(
            f"The JSON received is not valid: {e}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"An error has occurred while extracting the data: {e}"
        ) from e
