"""EXIF shot-time reader.

Extracts the moment a photo was taken from its EXIF metadata. A pure utility
with no GUI dependency.

Tag priority:
    1. ``DateTimeOriginal`` (36867) - when the shutter fired.
    2. ``DateTimeDigitized`` (36868) - when the image was digitized.
    3. ``DateTime`` (306) - last modification recorded by the camera/software.

Returns ``None`` whenever no usable shot time exists, so callers can route the
photo to the "others" folder.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

#: Exif IFD pointer tag; DateTimeOriginal/DateTimeDigitized live inside it.
_EXIF_IFD = 0x8769

_DATETIME_ORIGINAL = 36867
_DATETIME_DIGITIZED = 36868
_DATETIME = 306

#: EXIF timestamps are "YYYY:MM:DD HH:MM:SS".
_EXIF_FORMAT = "%Y:%m:%d %H:%M:%S"


def read_shot_time(path: str | Path) -> datetime | None:
    """Return when the photo was taken, or ``None`` if EXIF has no shot time.

    Never raises: any unreadable file or malformed metadata is reported as
    ``None`` so a single bad photo cannot abort a batch.

    Args:
        path: Image file to read.

    Returns:
        The shot time, or ``None`` if it is missing or unparsable.
    """
    try:
        from PIL import Image
    except ImportError:
        logger.debug("Pillow is not installed; EXIF cannot be read.")
        return None

    path = Path(path)
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            if not exif:
                return None
            raw = _find_raw_value(exif)
    except Exception:  # noqa: BLE001 - unreadable metadata -> no shot time
        logger.debug("Failed to read EXIF: %s", path, exc_info=True)
        return None

    if raw is None:
        return None
    return _parse(raw, path)


def _find_raw_value(exif) -> str | None:
    """Return the first present shot-time tag value in priority order."""
    try:
        ifd = exif.get_ifd(_EXIF_IFD)
    except Exception:  # noqa: BLE001 - some files have a broken Exif IFD
        ifd = {}

    for source, tag in (
        (ifd, _DATETIME_ORIGINAL),
        (ifd, _DATETIME_DIGITIZED),
        (exif, _DATETIME),
    ):
        value = source.get(tag)
        if value:
            return value
    return None


def _parse(raw, path: Path) -> datetime | None:
    """Parse an EXIF timestamp value into a ``datetime``."""
    if isinstance(raw, bytes):
        raw = raw.decode("ascii", errors="ignore")
    if not isinstance(raw, str):
        return None

    text = raw.strip().rstrip("\x00").strip()
    if not text:
        return None

    try:
        return datetime.strptime(text, _EXIF_FORMAT)
    except ValueError:
        # Cameras write placeholders such as "0000:00:00 00:00:00", and some
        # omit the time part entirely.
        try:
            return datetime.strptime(text[:10], "%Y:%m:%d")
        except ValueError:
            logger.debug("Unparsable EXIF timestamp %r: %s", text, path)
            return None
