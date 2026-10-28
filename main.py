"""import pandas as pd
import requests
import json

url = "https://apidatos.ree.es/es/datos/generacion/estructura-generacion?start_date=2014-01-01T00:00&end_date=2018-12-31T23:59&time_trunc=year&geo_trunc=electric_system&geo_limit=ccaa&geo_ids=7"

try:
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    records = list()
    energy_title = []
    energy_type = []
    for item in data.get("included", []):
        energy_title = item["attributes"]["title"]
        energy_type = item["attributes"]["type"]

        for value in item["attributes"]["values"]:
            records.append(
                {
                    "technology": energy_title,
                    "category": energy_type,
                    "datetime": value["datetime"],
                    "value_mwh": value["value"],
                    "percentage": round((value["percentage"] * 100), 2),
                }
            )
    df = pd.DataFrame(records)
    df["datetime"] = pd.to_datetime(df["datetime"])
    print(df)

except requests.exceptions.RequestException as e:
    print(f"An error has occurred: {e}")
"""