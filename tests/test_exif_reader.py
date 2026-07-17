"""Unit tests for reading the EXIF shot time."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from services.exif_reader import read_shot_time
from tests.conftest import write_corrupt_image, write_valid_image

pytest.importorskip("PIL")


def test_reads_datetime_original(tmp_path: Path):
    shot = datetime(2026, 7, 16, 14, 30, 5)
    path = write_valid_image(tmp_path / "a.jpg", shot_time=shot)
    assert read_shot_time(path) == shot


def test_image_without_exif_returns_none(tmp_path: Path):
    path = write_valid_image(tmp_path / "b.jpg")
    assert read_shot_time(path) is None


def test_corrupt_file_returns_none(tmp_path: Path):
    path = write_corrupt_image(tmp_path / "bad.jpg")
    assert read_shot_time(path) is None


def test_missing_file_returns_none(tmp_path: Path):
    assert read_shot_time(tmp_path / "nope.jpg") is None


def test_placeholder_timestamp_returns_none(tmp_path: Path):
    from PIL import Image

    from tests.conftest import EXIF_DATETIME_ORIGINAL

    path = tmp_path / "zero.jpg"
    image = Image.new("RGB", (8, 8))
    exif = image.getexif()
    exif.get_ifd(0x8769)[EXIF_DATETIME_ORIGINAL] = "0000:00:00 00:00:00"
    image.save(path, exif=exif)

    assert read_shot_time(path) is None
