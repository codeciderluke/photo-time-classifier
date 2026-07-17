"""File-processing service package.

Handles image scanning, EXIF shot-time reading, folder naming, and file
copying, separate from the GUI layer.
"""

from .categorizer import (
    DAMAGED,
    DAY,
    GRANULARITIES,
    MONTH,
    OTHERS,
    YEAR,
    build_subfolder,
)
from .exif_reader import read_shot_time
from .file_copy_service import FileCopyService
from .image_scanner import ImageScanner

__all__ = [
    "ImageScanner",
    "FileCopyService",
    "read_shot_time",
    "build_subfolder",
    "GRANULARITIES",
    "YEAR",
    "MONTH",
    "DAY",
    "OTHERS",
    "DAMAGED",
]
