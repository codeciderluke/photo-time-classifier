"""Shot-time classification pipeline shared by the GUI and CLI.

Scans a folder, reads each photo's EXIF shot time, and copies the images into
date subfolders. Has no GUI dependency: progress, logging, and stop are plain
callbacks.
"""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from filters import CORRUPT, PARTIAL, inspect_image
from services import (
    DAMAGED,
    DAY,
    GRANULARITIES,
    FileCopyService,
    ImageScanner,
    build_subfolder,
    read_shot_time,
)

logger = logging.getLogger(__name__)

ProgressCb = Callable[[int, int], None]
LogCb = Callable[[str], None]
StopCb = Callable[[], bool]


def _register_heif() -> None:
    """Enable reading HEIC/HEIF images through Pillow (iPhone photos)."""
    try:
        import pi_heif

        pi_heif.register_heif_opener()
    except Exception:  # noqa: BLE001 - HEIF support is optional
        pass


class PipelineError(RuntimeError):
    """Fatal error that aborts the whole job (e.g. a bad folder)."""


@dataclass
class ClassifyConfig:
    """Settings for a classification run."""

    source_folder: str
    destination_folder: str
    granularity: str = DAY
    recursive: bool = True


@dataclass
class ClassifySummary:
    """Counts after a run completes."""

    total: int = 0
    with_time: int = 0
    others: int = 0
    damaged: int = 0
    corrupt: int = 0
    failed: int = 0
    copied: int = 0
    stopped: bool = False
    category_counts: dict[str, int] = field(default_factory=dict)


def run_classification(
    config: ClassifyConfig,
    *,
    on_progress: ProgressCb | None = None,
    on_log: LogCb | None = None,
    should_stop: StopCb | None = None,
) -> ClassifySummary:
    """Run the full scan -> read EXIF -> copy pipeline.

    Photos carrying an EXIF shot time are copied into a folder named after that
    time (``2026`` / ``2026-07`` / ``2026-07-16``, per ``config.granularity``).
    Photos without one go to ``others``. Damaged photos - whether partially
    damaged or fully corrupt - are set aside in ``Damaged`` instead.

    Args:
        config: Run settings.
        on_progress: Called as ``(current, total)`` after each image.
        on_log: Called with a human-readable message per image/step.
        should_stop: Polled before each image; return ``True`` to stop early.

    Returns:
        A summary of the run.

    Raises:
        PipelineError: A fatal error (bad folder or bad option) aborted the run.
    """
    log: LogCb = on_log or (lambda _m: None)
    progress: ProgressCb = on_progress or (lambda _c, _t: None)
    stop: StopCb = should_stop or (lambda: False)

    if config.granularity not in GRANULARITIES:
        raise PipelineError(
            f"Unknown classification option: {config.granularity!r} "
            f"(use one of {', '.join(GRANULARITIES)})"
        )

    _register_heif()

    # 1) Collect images
    try:
        images = ImageScanner(recursive=config.recursive).scan(config.source_folder)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise PipelineError(f"Source folder error: {exc}") from exc

    summary = ClassifySummary(total=len(images))
    if summary.total == 0:
        log("No images to process.")
        return summary
    log(f"Found {summary.total} images.")
    log(f"Sorting by shot time ({config.granularity}).")

    # Files land directly in their date folder, so the source subfolder layout
    # is intentionally not recreated underneath it.
    copier = FileCopyService(
        config.source_folder, config.destination_folder, preserve_structure=False
    )
    counts: Counter[str] = Counter()

    def do_copy(image_path: Path, subfolder: str) -> bool:
        try:
            copier.copy(image_path, subfolder=subfolder)
            counts[subfolder] += 1
            return True
        except OSError as exc:
            log(f"[Copy failed] {image_path.name}: {exc}")
            return False

    def handle_image(image_path: Path, name: str) -> None:
        """Classify and copy one image. The loop wraps this so a single image
        can never stop the whole run."""
        level = inspect_image(image_path)
        if level in (CORRUPT, PARTIAL):
            if level == CORRUPT:
                summary.corrupt += 1
                prefix = "Corrupt"
            else:
                summary.damaged += 1
                prefix = "Partially damaged"
            if do_copy(image_path, DAMAGED):
                summary.copied += 1
                log(f"[{prefix} -> {DAMAGED}] {name}")
            return

        shot_time = read_shot_time(image_path)
        subfolder = build_subfolder(config.granularity, shot_time)

        if shot_time is None:
            summary.others += 1
            prefix = "No shot time"
        else:
            summary.with_time += 1
            prefix = shot_time.strftime("%Y-%m-%d %H:%M:%S")

        if do_copy(image_path, subfolder):
            summary.copied += 1
            log(f"[{prefix} -> {subfolder}] {name}")

    # 2) Process each image. A broad guard ensures no single image (or an
    # unexpected error in any library) can abort the entire run.
    for index, image_path in enumerate(images, start=1):
        if stop():
            summary.stopped = True
            break

        image_path = Path(image_path)
        name = image_path.name
        try:
            handle_image(image_path, name)
        except Exception as exc:  # noqa: BLE001 - never let one image kill the run
            summary.failed += 1
            log(f"[Error] {name}: {exc}")
        progress(index, summary.total)

    summary.category_counts = dict(counts)
    return summary
