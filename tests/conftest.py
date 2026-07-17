"""Shared test fixtures and image builders."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

# Invalid (corrupt) image bytes.
CORRUPT_IMAGE_BYTES = b"this is definitely not a valid image file"

#: EXIF DateTimeOriginal tag, and the Exif IFD that holds it.
EXIF_DATETIME_ORIGINAL = 36867


def write_valid_image(path: Path, shot_time: datetime | None = None) -> Path:
    """Create a valid image file that passes the integrity check.

    Args:
        path: Where to write the image.
        shot_time: If given, embed it as EXIF ``DateTimeOriginal``. Otherwise
            the image carries no shot time.

    With Pillow, writes a real valid image (integrity check active); otherwise
    writes arbitrary bytes (in which case the integrity check is skipped).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        path.write_bytes(b"placeholder-image-bytes")
        return path

    return _write_jpeg(path, size=(8, 8), shot_time=shot_time)


def _write_jpeg(path: Path, size: tuple[int, int], shot_time: datetime | None) -> Path:
    """Write a real image, embedding ``shot_time`` as EXIF when given."""
    from PIL import Image

    image = Image.new("RGB", size, (20, 20, 20))
    if shot_time is None:
        image.save(path, quality=95)
        return path

    exif = image.getexif()
    exif_ifd = exif.get_ifd(0x8769)
    exif_ifd[EXIF_DATETIME_ORIGINAL] = shot_time.strftime("%Y:%m:%d %H:%M:%S")
    image.save(path, exif=exif, quality=95)
    return path


def write_corrupt_image(path: Path) -> Path:
    """Create a corrupt (undecodable) image file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(CORRUPT_IMAGE_BYTES)
    return path


def write_truncated_image(path: Path, shot_time: datetime | None = None) -> Path:
    """Create a partially damaged image: a valid header with truncated pixels.

    Args:
        path: Where to write the image.
        shot_time: If given, embed it as EXIF ``DateTimeOriginal``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        path.write_bytes(b"placeholder-image-bytes")
        return path

    # Big enough that cutting the tail leaves the header intact but the pixel
    # data incomplete; an 8x8 image is too small to truncate meaningfully.
    source = path.with_name(f"_full_{path.name}")
    _write_jpeg(source, size=(240, 240), shot_time=shot_time)
    data = source.read_bytes()
    source.unlink()
    path.write_bytes(data[: int(len(data) * 0.6)])
    return path
