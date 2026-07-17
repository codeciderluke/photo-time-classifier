"""Command-line interface for Photo Time Classifier.

Runs the same classification pipeline as the GUI, without any GUI dependency.

Examples:
    python cli.py ./photos ./sorted            # sort by day (default)
    python cli.py ./photos ./sorted --year     # sort into 2026/
    python cli.py ./photos ./sorted --month    # sort into 2026-07/
    python cli.py ./photos ./sorted --day --no-recursive --quiet
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys

from core import ClassifyConfig, PipelineError, run_classification
from services import DAY, MONTH, YEAR


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="photo-time-classifier",
        description=(
            "Sort photos into folders by the shot time recorded in their EXIF "
            "data. Photos with no shot time go to 'others'; damaged files go "
            "to 'Damaged'."
        ),
    )
    p.add_argument("source", help="Folder of images to scan.")
    p.add_argument("destination", help="Folder to copy results into.")

    # Exactly one granularity, mirroring the GUI's radio buttons.
    group = p.add_mutually_exclusive_group()
    group.add_argument("--year", dest="granularity", action="store_const", const=YEAR,
                       help="Sort into year folders (2026).")
    group.add_argument("--month", dest="granularity", action="store_const", const=MONTH,
                       help="Sort into year-month folders (2026-07).")
    group.add_argument("--day", dest="granularity", action="store_const", const=DAY,
                       help="Sort into year-month-day folders (2026-07-16). Default.")
    p.set_defaults(granularity=DAY)

    p.add_argument("--no-recursive", action="store_true",
                   help="Do not scan subfolders.")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="Show only a progress bar, not per-image lines.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    config = ClassifyConfig(
        source_folder=args.source,
        destination_folder=args.destination,
        granularity=args.granularity,
        recursive=not args.no_recursive,
    )

    # Ctrl+C requests a graceful stop (finish the current image, print summary).
    state = {"stop": False}
    signal.signal(signal.SIGINT, lambda *_: state.__setitem__("stop", True))

    def on_log(message: str) -> None:
        if not args.quiet:
            print(message)

    def on_progress(current: int, total: int) -> None:
        if args.quiet:
            pct = int(current / total * 100) if total else 0
            bar = "#" * (pct // 4)
            print(f"\r[{bar:<25}] {pct:3d}%  ({current}/{total})", end="", flush=True)

    try:
        summary = run_classification(
            config,
            on_progress=on_progress,
            on_log=on_log,
            should_stop=lambda: state["stop"],
        )
    except PipelineError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1

    if args.quiet:
        print()

    state_label = "Stopped" if summary.stopped else "Done"
    print(
        f"\n{state_label}: total {summary.total} | with shot time {summary.with_time} | "
        f"others {summary.others} | partially damaged {summary.damaged} | "
        f"corrupt {summary.corrupt} | copied {summary.copied} | "
        f"failed {summary.failed}"
    )
    if summary.category_counts:
        print("Folder breakdown:")
        for category, count in sorted(summary.category_counts.items()):
            print(f"  {category}: {count}")

    return 0


if __name__ == "__main__":
    # Required for frozen builds so a spawned worker process does not re-run
    # the whole program.
    import multiprocessing

    multiprocessing.freeze_support()
    raise SystemExit(main())
