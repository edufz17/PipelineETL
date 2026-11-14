import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

REQUIRED_VARIABLES = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


def get_connection_params() -> dict[str, str | int]:
    missing = [name for name in REQUIRED_VARIABLES if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "connect_timeout": 5,
    }


def _validate_env() -> None:
    missing = [name for name in REQUIRED_VARIABLES if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")


def get_connection() -> psycopg.Connection:
    _validate_env()
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def test_connection() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_user, current_database(), version()")
            row = cur.fetchone()

    if row:
        print(f"Connected as '{row[0]}' to database '{row[1]}'")
        print(row[2])


if __name__ == "__main__":
    test_connection()
