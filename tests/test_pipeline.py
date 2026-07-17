"""Unit tests for the shared shot-time classification pipeline."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from core import ClassifyConfig, PipelineError, run_classification
from services import DAMAGED, DAY, MONTH, YEAR
from tests.conftest import write_corrupt_image, write_truncated_image, write_valid_image

pytest.importorskip("PIL")

SHOT = datetime(2026, 7, 16, 14, 30, 5)


def _config(src: Path, dst: Path, **kw) -> ClassifyConfig:
    return ClassifyConfig(source_folder=str(src), destination_folder=str(dst), **kw)


def test_sorts_into_day_folder(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_valid_image(src / "a.jpg", shot_time=SHOT)

    summary = run_classification(_config(src, dst, granularity=DAY))

    assert summary.with_time == 1
    assert summary.copied == 1
    assert (dst / "2026-07-16" / "a.jpg").exists()


def test_sorts_into_month_folder(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_valid_image(src / "a.jpg", shot_time=SHOT)

    run_classification(_config(src, dst, granularity=MONTH))

    assert (dst / "2026-07" / "a.jpg").exists()


def test_sorts_into_year_folder(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_valid_image(src / "a.jpg", shot_time=SHOT)

    run_classification(_config(src, dst, granularity=YEAR))

    assert (dst / "2026" / "a.jpg").exists()


def test_photo_without_exif_goes_to_others(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_valid_image(src / "no_exif.jpg")

    summary = run_classification(_config(src, dst))

    assert summary.others == 1
    assert summary.with_time == 0
    assert (dst / "others" / "no_exif.jpg").exists()


def test_mixed_batch_splits_by_date_and_others(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_valid_image(src / "a.jpg", shot_time=SHOT)
    write_valid_image(src / "b.jpg", shot_time=datetime(2025, 12, 24, 9, 0, 0))
    write_valid_image(src / "c.jpg")

    summary = run_classification(_config(src, dst, granularity=DAY))

    assert summary.total == 3
    assert summary.copied == 3
    assert (dst / "2026-07-16" / "a.jpg").exists()
    assert (dst / "2025-12-24" / "b.jpg").exists()
    assert (dst / "others" / "c.jpg").exists()
    assert summary.category_counts == {
        "2026-07-16": 1,
        "2025-12-24": 1,
        "others": 1,
    }


def test_subfolder_photos_land_flat_in_date_folder(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_valid_image(src / "trip" / "a.jpg", shot_time=SHOT)

    run_classification(_config(src, dst, granularity=DAY))

    # The source layout is not recreated under the date folder.
    assert (dst / "2026-07-16" / "a.jpg").exists()


def test_same_name_photos_are_deduplicated(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_valid_image(src / "one" / "a.jpg", shot_time=SHOT)
    write_valid_image(src / "two" / "a.jpg", shot_time=SHOT)

    summary = run_classification(_config(src, dst, granularity=DAY))

    assert summary.copied == 2
    assert (dst / "2026-07-16" / "a.jpg").exists()
    assert (dst / "2026-07-16" / "a_1.jpg").exists()


def test_corrupt_image_goes_to_damaged(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_corrupt_image(src / "bad.jpg")

    summary = run_classification(_config(src, dst))

    assert summary.corrupt == 1
    assert summary.copied == 1
    assert (dst / DAMAGED / "bad.jpg").exists()


def test_partially_damaged_image_goes_to_damaged(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_truncated_image(src / "cut.jpg", shot_time=SHOT)

    summary = run_classification(_config(src, dst))

    assert summary.damaged == 1
    assert summary.copied == 1
    # A damaged photo is set aside even though it carries a shot time.
    assert (dst / DAMAGED / "cut.jpg").exists()
    assert not (dst / "2026-07-16" / "cut.jpg").exists()


def test_missing_source_raises_pipeline_error(tmp_path: Path):
    with pytest.raises(PipelineError):
        run_classification(_config(tmp_path / "nope", tmp_path / "dst"))


def test_unknown_granularity_raises_pipeline_error(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    with pytest.raises(PipelineError):
        run_classification(_config(src, dst, granularity="hour"))


def test_empty_source_returns_zero(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    summary = run_classification(_config(src, dst))
    assert summary.total == 0
    assert summary.copied == 0


def test_non_recursive_skips_subfolders(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write_valid_image(src / "top.jpg", shot_time=SHOT)
    write_valid_image(src / "deep" / "nested.jpg", shot_time=SHOT)

    summary = run_classification(_config(src, dst, recursive=False))

    assert summary.total == 1
    assert (dst / "2026-07-16" / "top.jpg").exists()


def test_stop_callback_halts(tmp_path: Path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    for i in range(5):
        write_valid_image(src / f"img_{i}.jpg", shot_time=SHOT)

    calls = {"n": 0}

    def should_stop() -> bool:
        calls["n"] += 1
        return calls["n"] > 2

    summary = run_classification(_config(src, dst), should_stop=should_stop)
    assert summary.stopped is True
