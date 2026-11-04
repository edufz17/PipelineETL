import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

REQUIRED_VARIABLES = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


def build_database_url() -> URL:
    missing = [name for name in REQUIRED_VARIABLES if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    return URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )


def get_engine() -> Engine:
    return create_engine(
        build_database_url(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


engine = get_engine()


def test_connection(engine_to_test: Engine = engine) -> None:
    with engine_to_test.connect() as connection:
        row = connection.execute(
            text("SELECT current_user, current_database(), version()")
        ).one()

    print(f"Connected as '{row[0]}' to database '{row[1]}'")
    print(row[2])


if __name__ == "__main__":
    test_connection()
