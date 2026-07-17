"""Unit tests for shot-time folder naming (``build_subfolder``)."""

from __future__ import annotations

from datetime import datetime

import pytest

from services.categorizer import DAY, MONTH, OTHERS, YEAR, build_subfolder

SHOT = datetime(2026, 7, 16, 14, 30, 5)


# ------------------------------------------------------------- granularity

def test_year_folder():
    assert build_subfolder(YEAR, SHOT) == "2026"


def test_month_folder():
    assert build_subfolder(MONTH, SHOT) == "2026-07"


def test_day_folder():
    assert build_subfolder(DAY, SHOT) == "2026-07-16"


def test_month_and_day_are_zero_padded():
    shot = datetime(2026, 1, 3, 0, 0, 0)
    assert build_subfolder(MONTH, shot) == "2026-01"
    assert build_subfolder(DAY, shot) == "2026-01-03"


# ---------------------------------------------------------------- no EXIF

@pytest.mark.parametrize("granularity", [YEAR, MONTH, DAY])
def test_missing_shot_time_goes_to_others(granularity):
    assert build_subfolder(granularity, None) == OTHERS


# --------------------------------------------------------- invalid option

def test_unknown_granularity_raises():
    with pytest.raises(ValueError):
        build_subfolder("hour", SHOT)
