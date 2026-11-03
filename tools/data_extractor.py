from datetime import date

import requests
import pandas as pd


def extract_data(url: str) -> pd.DataFrame:
    last_update = str()
    try:
        response = requests.get(
            url=url,
            timeout=(5, 30),
        )
        response.raise_for_status()

        data = response.json()
        records = list()
        spot_market_records = list()

        for item in data.get("included", []):
            attributes = item.get("attributes", [])
            pricing_type = item["type"]
            type_id = item["id"]
            for value in attributes.get("values", []):
                records.append(
                    {
                        "type": pricing_type,
                        "id": type_id,
                        "datetime": value["datetime"],
                        "value": value["value"],
                        # "percentage": round((value["percentage"] * 100), 2),
                    }
                )

    except requests.exceptions.RequestException as e:
        print(f"An error has occurred while contacting the API: {e}")
    df = pd.DataFrame(records)
    df["datetime"] = pd.to_datetime(df["datetime"])

    return df


url = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real?start_date=2026-10-27T00:00&end_date=2026-10-27T23:59&time_trunc=hour"

df = pd.DataFrame(extract_data(url))
print(df)
