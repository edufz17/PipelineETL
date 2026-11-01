import pandas as pd
from tools import data_extractor

url = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real?start_date=2026-10-27T00:00&end_date=2026-10-27T23:59&time_trunc=hour"

df = pd.DataFrame(data_extractor.extract_data(url))
print(df.head(26))
