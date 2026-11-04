BASE_URL = "https://apidatos.ree.es"
ENDPOINT = "/es/datos/mercados/precios-mercados-tiempo-real"
API_URL = f"{BASE_URL}{ENDPOINT}"

GEO_TRUNC = "electric_system"  # With the actual type of JSON response (only including PVPC) it's not necessary.
GEO_LIMIT = "peninsular"
GEO_IDS = "8741"

TIMEOUT = (5, 30)

VALID_TIME_TRUNCS = {"hour", "day", "month", "year"}

PRICE_UNIT = "EUR/MWh"
