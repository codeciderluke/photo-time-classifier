"""GUI entry point.

Logging handlers and log level are configured only here. Service modules obtain
a logger but never configure handlers.
"""

from __future__ import annotations

import io
import logging
import os
import sys


def repair_std_streams() -> None:
    """Give the process valid stdio handles.

    A windowed (``--noconsole``) frozen build has no console, so stdin/out/err
    are invalid and anything writing to them (such as logging) can fail. Point
    the handles at devnull.
    """
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        fd = os.open(os.devnull, os.O_RDWR)
        for target in (0, 1, 2):
            try:
                os.dup2(fd, target)
            except OSError:
                pass
    except OSError:
        pass
    for name, mode in (("stdin", "r"), ("stdout", "w"), ("stderr", "w")):
        if getattr(sys, name, None) is None:
            try:
                setattr(sys, name, io.TextIOWrapper(open(os.devnull, mode + "b")))
            except OSError:
                pass


def configure_logging(level: int = logging.INFO) -> None:
    """Configure application-wide logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    """Run the GUI application."""
    repair_std_streams()
    configure_logging()

    from pathlib import Path

    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QApplication

    from gui import MainWindow

    app = QApplication(sys.argv)
    icon_path = Path(__file__).resolve().parent / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
