"""Compute the destination subfolder path.

Given the shot time and the selected granularity (year / month / day), decides
the folder where the image should be saved. Contains no EXIF-reading logic.
"""

from __future__ import annotations

from datetime import datetime

# Granularity options (exactly one is active per run).
YEAR = "year"
MONTH = "month"
DAY = "day"

#: Valid granularity values.
GRANULARITIES: tuple[str, ...] = (YEAR, MONTH, DAY)

#: Folder-name pattern per granularity, e.g. 2026 / 2026-07 / 2026-07-16.
_PATTERNS: dict[str, str] = {
    YEAR: "%Y",
    MONTH: "%Y-%m",
    DAY: "%Y-%m-%d",
}

# Category folder names
OTHERS = "others"  # photos with no EXIF shot time
DAMAGED = "Damaged"  # damaged photos (partially damaged or fully corrupt)


def build_subfolder(granularity: str, shot_time: datetime | None) -> str:
    """Compute the relative subfolder where the image should be saved.

    Rules:
        - No shot time -> ``others``.
        - ``year`` -> ``2026``.
        - ``month`` -> ``2026-07``.
        - ``day`` -> ``2026-07-16``.

    Args:
        granularity: One of ``year``, ``month``, ``day``.
        shot_time: When the photo was taken, or ``None`` if EXIF has none.

    Returns:
        The relative subfolder name under the destination root.

    Raises:
        ValueError: If ``granularity`` is not a known option.
    """
    pattern = _PATTERNS.get(granularity)
    if pattern is None:
        raise ValueError(
            f"Unknown granularity: {granularity!r} (use one of {', '.join(GRANULARITIES)})"
        )

    if shot_time is None:
        return OTHERS
    return shot_time.strftime(pattern)
