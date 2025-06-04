import pytest
from freezegun import freeze_time
from datetime import datetime

from filtertool import months_since


@freeze_time("2025-05-20")
def test_months_since_valid_date_same_month():
    assert months_since("2025-05-01T00:00:00.000") == "0"

@freeze_time("2025-05-20")
def test_months_since_one_month_before():
    assert months_since("2025-04-01T00:00:00.000") == "1"

@freeze_time("2025-05-20")
def test_months_since_several_months():
    assert months_since("2024-11-01T00:00:00.000") == "6"

@freeze_time("2025-05-20")
def test_months_since_previous_year():
    assert months_since("2024-05-01T00:00:00.000") == "12"

@freeze_time("2025-05-20")
def test_months_since_two_previous_year():
    assert months_since("2023-05-01T00:00:00.000") == "24"

@freeze_time("2025-05-20")
def test_months_since_future_date():
    assert months_since("2026-01-01T00:00:00.000") == "0"

@freeze_time("2025-05-20")
def test_months_since_invalid_format():
    assert months_since("not-a-date") == ""

@freeze_time("2025-05-20")
def test_months_since_empty_string():
    assert months_since("") == ""

@freeze_time("2025-05-20")
def test_months_since_none():
    assert months_since(None) == ""
