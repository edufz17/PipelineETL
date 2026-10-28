import requests
import pandas as pd


def extract_data(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url=url)
        response.raise_for_status()

        data = response.json()

        records = list()
        for item in data.get("included", []):

            for value in item["attributes"]["content"]:
                technology = value["type"]
                category = value["groupId"]
                for nums in value["attributes"]["values"]:
                    records.append(
                        {
                            "technology": technology,
                            "category": category,
                            "datetime": nums["datetime"],
                            "value_mwh": nums["value"],
                            "percentage": round((nums["percentage"] * 100), 2),
                        }
                    )
    except requests.exceptions.RequestException as e:
        print(f"An error has occurred while contacting the API: {e}")

    df = pd.DataFrame(records)
    df["datetime"] = pd.to_datetime(df["datetime"])

    return df
