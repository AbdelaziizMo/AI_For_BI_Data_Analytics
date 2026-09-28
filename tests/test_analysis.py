import json

from src.config import OUTPUT_DIR


RESULT_FILE = OUTPUT_DIR / "aggregated_results.json"


def load_results():
    with open(RESULT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def test_aggregated_results_file_exists():
    assert RESULT_FILE.exists()


def test_aggregated_results_has_required_structure():
    data = load_results()

    required_fields = {
        "business_question",
        "analysis_type",
        "dimensions",
        "kpis",
        "top_n",
        "date_range",
        "row_count",
        "results",
    }

    assert required_fields.issubset(data.keys())


def test_analysis_returns_rows():
    data = load_results()

    assert data["row_count"] > 0
    assert len(data["results"]) > 0


def test_analysis_row_count_is_consistent():
    data = load_results()

    assert data["row_count"] == len(data["results"])


def test_service_trend_contains_expected_dimensions():
    data = load_results()

    assert data["analysis_type"] == "SERVICE_TREND"
    assert "SERVICE" in data["dimensions"]
    assert "DATE" in data["dimensions"]


def test_top_n_is_valid():
    data = load_results()

    assert isinstance(data["top_n"], int)
    assert data["top_n"] > 0
