
import pandas as pd
from tools import data_extractor

url = "https://apidatos.ree.es/es/datos/generacion/estructura-generacion"

df = pd.DataFrame(data_extractor.extract_data(url,params))
print(df)
