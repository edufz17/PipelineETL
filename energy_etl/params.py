from dataclasses import dataclass
from datetime import datetime

from energy_etl.config import GEO_IDS, GEO_LIMIT, GEO_TRUNC, VALID_TIME_TRUNCS


@dataclass(frozen=True)
class QueryParams:
    start_date: datetime
    end_date: datetime
    time_trunc: str = "hour"
    geo_trunc: str = GEO_TRUNC
    geo_limit: str = GEO_LIMIT
    geo_ids: str = GEO_IDS

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("End date can't be before start date.")
        if self.time_trunc not in VALID_TIME_TRUNCS:
            raise ValueError(f"Time trunc not valid. Available: {VALID_TIME_TRUNCS}")
        if not self.geo_ids:
            raise ValueError("geo_ids can't be empty.")

    def to_request_params(self) -> dict[str, str]:
        return {
            "start_date": self.start_date.strftime("%Y-%m-%dT00:00"),
            "end_date": self.end_date.strftime("%Y-%m-%dT23:59"),
            "time_trunc": self.time_trunc,
            "geo_trunc": self.geo_trunc,
            "geo_limit": self.geo_limit,
            "geo_ids": self.geo_ids,
        }
