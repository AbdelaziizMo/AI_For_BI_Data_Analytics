import json

from src.config import OUTPUT_DIR


RESULT_FILE = OUTPUT_DIR / "aggregated_results.json"


EXPECTED_KPIS = {
    "TOTAL_REVENUE",
    "TRANSACTION_VOLUME",
    "REVENUE_SHARE",
    "VOLUME_SHARE",
    "REVENUE_GROWTH",
    "VOLUME_GROWTH",
    "REVENUE_RANK",
    "VOLUME_RANK",
}


EXPECTED_RESULT_FIELDS = {
    "Total_Revenue",
    "Total_Transaction_Volume",
    "Revenue_Share",
    "Volume_Share",
    "Revenue_Growth",
    "Volume_Growth",
    "Revenue_Rank",
    "Volume_Rank",
}


def load_results():
    with open(RESULT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def test_all_planned_kpis_are_defined():
    data = load_results()

    actual_kpis = set(data["kpis"])

    assert EXPECTED_KPIS.issubset(actual_kpis)


def test_all_kpi_fields_exist_in_results():
    data = load_results()

    assert len(data["results"]) > 0

    result_fields = set(data["results"][0].keys())

    assert EXPECTED_RESULT_FIELDS.issubset(result_fields)


def test_revenue_share_is_valid():
    data = load_results()

    for row in data["results"]:
        value = row["Revenue_Share"]

        assert value is None or 0 <= value <= 100


def test_volume_share_is_valid():
    data = load_results()

    for row in data["results"]:
        value = row["Volume_Share"]

        assert value is None or 0 <= value <= 100


def test_ranks_are_positive():
    data = load_results()

    for row in data["results"]:
        assert row["Revenue_Rank"] is None or row["Revenue_Rank"] > 0
        assert row["Volume_Rank"] is None or row["Volume_Rank"] > 0

