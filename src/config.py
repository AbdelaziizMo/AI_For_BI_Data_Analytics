import os
from pathlib import Path

from dotenv import load_dotenv


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")


# Database configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SERVICE = os.getenv("DB_SERVICE")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Date range configuration
START_DATE = os.getenv(
    "START_DATE",
    "2026-07-07 00:00:00",
)

END_DATE = os.getenv(
    "END_DATE",
    "2026-07-13 00:00:00",
)

# Project directories
OUTPUT_DIR = BASE_DIR / "output"


# Output files
EXCEL_REPORT_FILE = OUTPUT_DIR / "data_quality_report.xlsx"


def validate_config():
    """Validate required environment variables."""

    required_variables = {
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
        "DB_HOST": DB_HOST,
        "DB_SERVICE": DB_SERVICE,
        "GEMINI_API_KEY": GEMINI_API_KEY
    }
    
    missing_variables = [
        name
        for name, value in required_variables.items()
        if not value
    ]

    if missing_variables:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing_variables)
        )