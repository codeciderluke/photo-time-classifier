"""Main application window.

Handles only folder selection, settings input, progress display, log display,
and start/stop. The actual classification work is delegated to
``ClassifyWorker``.
"""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core import ClassifyConfig, ClassifySummary
from services import DAY, MONTH, YEAR

from .classify_worker import ClassifyWorker
from .theme import build_stylesheet

APP_TITLE = "Photo Time Classifier"


class MainWindow(QWidget):
    """Main window of the Photo Time Classifier."""

    def __init__(self) -> None:
        super().__init__()
        self._worker: ClassifyWorker | None = None

        self.setWindowTitle(APP_TITLE)
        self.setObjectName("root")
        self._apply_icon()
        # Default size optimized for a Full HD (1920x1080) screen
        self.setMinimumSize(1100, 720)
        self.resize(1440, 900)
        self.setStyleSheet(build_stylesheet())

        self._build_ui()
        self._center_on_screen()

    def _apply_icon(self) -> None:
        """Set the window icon if the asset is available."""
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _center_on_screen(self) -> None:
        """Center the window on the current screen."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 32, 40, 32)
        outer.setSpacing(24)

        outer.addLayout(self._build_header())

        # Two-column body: left = settings/actions, right = log
        body = QHBoxLayout()
        body.setSpacing(24)

        left = QVBoxLayout()
        left.setSpacing(24)
        left.addWidget(self._build_settings_card())
        left.addWidget(self._build_action_card())
        left.addStretch(1)

        left_wrap = QWidget()
        left_wrap.setLayout(left)
        left_wrap.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        body.addWidget(left_wrap, stretch=5)
        body.addWidget(self._build_log_card(), stretch=4)

        outer.addLayout(body, stretch=1)

        footer = QLabel("Designed by Codecider Lab")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        outer.addWidget(footer)

    def _build_header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        header.setSpacing(4)

        title = QLabel(APP_TITLE)
        title.setObjectName("title")

        subtitle = QLabel(
            "Sorts photos into folders by the shot time recorded in their EXIF data."
        )
        subtitle.setObjectName("subtitle")

        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        return card, layout

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    def _build_settings_card(self) -> QFrame:
        card, layout = self._card()

        # --- Folder selection ---
        layout.addWidget(self._section_label("FOLDERS"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Select a source folder")
        self.source_edit.setReadOnly(True)
        source_btn = QPushButton("Browse")
        source_btn.clicked.connect(self._pick_source)

        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("Select the destination folder")
        self.dest_edit.setReadOnly(True)
        dest_btn = QPushButton("Browse")
        dest_btn.clicked.connect(self._pick_destination)

        grid.addWidget(self._field_label("Source"), 0, 0)
        grid.addWidget(self.source_edit, 0, 1)
        grid.addWidget(source_btn, 0, 2)
        grid.addWidget(self._field_label("Destination"), 1, 0)
        grid.addWidget(self.dest_edit, 1, 1)
        grid.addWidget(dest_btn, 1, 2)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        # --- Scan settings ---
        layout.addSpacing(4)
        layout.addWidget(self._section_label("SCAN"))

        self.recursive_check = QCheckBox("Search subfolders")
        self.recursive_check.setChecked(True)
        layout.addWidget(self.recursive_check)

        # --- Classification options ---
        layout.addSpacing(4)
        layout.addWidget(self._section_label("CLASSIFICATION"))

        hint = QLabel(
            "Photos are sorted by EXIF shot time. Pick one option; photos with "
            "no shot time go to 'others', and damaged files go to 'Damaged'."
        )
        hint.setObjectName("subtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Exactly one granularity can be active, so these are radio buttons in
        # an exclusive group.
        self.year_radio = QRadioButton("Year  (e.g. 2026)")
        self.month_radio = QRadioButton("Month  (e.g. 2026-07)")
        self.day_radio = QRadioButton("Day  (e.g. 2026-07-16)")
        self.day_radio.setChecked(True)

        self.granularity_group = QButtonGroup(self)
        self.granularity_group.setExclusive(True)
        for button, value in (
            (self.year_radio, YEAR),
            (self.month_radio, MONTH),
            (self.day_radio, DAY),
        ):
            self.granularity_group.addButton(button)
            button.setProperty("granularity", value)
            layout.addWidget(button)

        return card

    def _selected_granularity(self) -> str:
        button = self.granularity_group.checkedButton()
        if button is None:
            return DAY
        return str(button.property("granularity"))

    def _build_action_card(self) -> QFrame:
        card, layout = self._card()

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._start)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)

        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addStretch(1)

        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("subtitle")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        buttons.addWidget(self.status_label)

        layout.addLayout(buttons)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        return card

    def _build_log_card(self) -> QFrame:
        card, layout = self._card()
        layout.addWidget(self._section_label("LOG"))

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("log")
        self.log_view.setReadOnly(True)
        # Cap history so very large batches don't grow memory without bound.
        self.log_view.setMaximumBlockCount(5000)
        layout.addWidget(self.log_view, stretch=1)

        return card

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    # -------------------------------------------------------------- actions

    def _pick_source(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select a source folder")
        if folder:
            self.source_edit.setText(folder)

    def _pick_destination(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select the destination folder"
        )
        if folder:
            self.dest_edit.setText(folder)

    def _append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def _start(self) -> None:
        source = self.source_edit.text().strip()
        destination = self.dest_edit.text().strip()

        if not source:
            self._warn("Please select a source folder.")
            return
        if not destination:
            self._warn("Please select a destination folder.")
            return
        if source == destination:
            self._warn("Source and destination folders must be different.")
            return

        config = ClassifyConfig(
            source_folder=source,
            destination_folder=destination,
            granularity=self._selected_granularity(),
            recursive=self.recursive_check.isChecked(),
        )

        self._worker = ClassifyWorker(config)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._append_log)
        self._worker.finished_summary.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._on_thread_done)

        self._set_running(True)
        self.log_view.clear()
        self.progress.setValue(0)
        self.status_label.setText("Classifying...")
        self._worker.start()

    def _stop(self) -> None:
        if self._worker is not None:
            self._worker.request_stop()
            self.stop_btn.setEnabled(False)

    # --------------------------------------------------------- worker slots

    def _on_progress(self, current: int, total: int) -> None:
        percent = int(current / total * 100) if total else 0
        self.progress.setValue(percent)
        self.status_label.setText(f"{current} / {total}  ·  {percent}%")

    def _on_finished(self, summary: ClassifySummary) -> None:
        state = "Stopped" if summary.stopped else "Done"
        self.status_label.setText(state)
        if not summary.stopped:
            self.progress.setValue(100)
        self._append_log(
            f"-- {state}: total {summary.total} · "
            f"with shot time {summary.with_time} · others {summary.others} · "
            f"partially damaged {summary.damaged} · corrupt {summary.corrupt} · "
            f"copied {summary.copied} · failed {summary.failed}"
        )
        # Show per-folder counts
        if summary.category_counts:
            for category, count in sorted(summary.category_counts.items()):
                self._append_log(f"    · {category}: {count}")

    def _on_failed(self, message: str) -> None:
        self.status_label.setText("Error")
        self._append_log(f"[Error] {message}")
        self._warn(message, title="Stopped")

    def _on_thread_done(self) -> None:
        self._set_running(False)
        self._worker = None

    # ---------------------------------------------------------------- utils

    def _set_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        for widget in (
            self.source_edit,
            self.dest_edit,
            self.recursive_check,
            self.year_radio,
            self.month_radio,
            self.day_radio,
        ):
            widget.setEnabled(not running)

    def _warn(self, message: str, title: str = "Notice") -> None:
        QMessageBox.warning(self, title, message)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        """Safely clean up a running worker when the window closes."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_stop()
            self._worker.wait(3000)
        event.accept()
