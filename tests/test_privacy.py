import pytest

from src.privacy_guard import (
    BLOCKED_FIELDS,
    ALLOWED_FIELDS,
    validate_no_blocked_fields,
    sanitize_results,
)


def test_blocked_fields_are_detected():
    results = [
        {
            "Service_Name": "Balance Transfer",
            "TransactionID": "TX-001",
        }
    ]

    with pytest.raises(ValueError):
        validate_no_blocked_fields(results)


def test_clean_aggregated_data_passes_privacy_check():
    results = [
        {
            "Service_Name": "Balance Transfer",
            "Daily_Revenue": 100000,
            "Daily_Transaction_Volume": 500,
        }
    ]

    validate_no_blocked_fields(results)


def test_sanitization_removes_unapproved_fields():
    results = [
        {
            "Service_Name": "Balance Transfer",
            "Daily_Revenue": 100000,
            "TransactionID": "TX-001",
        }
    ]

    sanitized = sanitize_results(results)

    assert "TransactionID" not in sanitized[0]
    assert "Service_Name" in sanitized[0]
    assert "Daily_Revenue" in sanitized[0]


def test_sanitized_data_contains_only_allowed_fields():
    results = [
        {
            "Service_Name": "Balance Transfer",
            "Daily_Revenue": 100000,
            "Daily_Transaction_Volume": 500,
        }
    ]

    sanitized = sanitize_results(results)

    for row in sanitized:
        assert set(row.keys()).issubset(ALLOWED_FIELDS)


def test_blocked_fields_are_not_allowed():
    assert BLOCKED_FIELDS.isdisjoint(ALLOWED_FIELDS)