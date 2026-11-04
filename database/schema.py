from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Double,
    Index,
    MetaData,
    Numeric,
    Table,
    Text,
    UniqueConstraint,
    func,
)

metadata = MetaData()

energy_prices = Table(
    "energy_prices",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("metric_id", Text, nullable=False),
    Column("metric_type", Text, nullable=False),
    Column("datetime_utc", DateTime(timezone=True), nullable=False),
    Column("value", Numeric(12, 4), nullable=False),
    Column("unit", Text, nullable=False),
    Column("geo_limit", Text, nullable=True),
    Column("percentage", Double, nullable=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    UniqueConstraint(
        "metric_id",
        "datetime_utc",
        name="uq_energy_prices_metric_datetime",
    ),
    Index("ix_energy_prices_datetime_utc", "datetime_utc"),
)
