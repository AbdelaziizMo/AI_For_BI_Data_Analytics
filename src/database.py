from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from src.config import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_SERVICE,
    validate_config,
)

def get_engine():
    """Create and return a SQLAlchemy Oracle engine."""

    validate_config()

    connection_url = URL.create(
        "oracle+oracledb",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        query={
            "service_name": DB_SERVICE
        },
    )

    return create_engine(
        connection_url,
        pool_pre_ping=True,
    )