"""Generate USER_MANUAL.pdf with ReportLab.

Keeping the manual as a script means it can be regenerated whenever the app
changes, instead of being hand-edited in a PDF editor. The screenshot on the
interface page is read from assets/, so refreshing that asset refreshes the
manual too.

Needs ReportLab, which the app itself does not use:

    pip install reportlab

    python build_manual.py            # writes USER_MANUAL.pdf
    python build_manual.py out.pdf    # writes somewhere else
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent

TITLE = "Photo Time Classifier"
SUBTITLE = "Sort photos by the time they were taken"
DOC_TITLE = f"{TITLE} - User Manual"

# Matches the app's dark theme (see gui/theme.py).
ACCENT = colors.HexColor("#3d8bfd")
INK = colors.HexColor("#171a21")
MUTED = colors.HexColor("#5b6478")
RULE = colors.HexColor("#d8dde8")
BAND = colors.HexColor("#0f1115")
ZEBRA = colors.HexColor("#f4f6fb")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


# --------------------------------------------------------------- styles

def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["BodyText"]
    return {
        "body": ParagraphStyle(
            "body", parent=base, fontName="Helvetica", fontSize=9.5,
            leading=14, textColor=INK, spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "h1", fontName="Helvetica-Bold", fontSize=15, leading=19,
            textColor=INK, spaceBefore=14, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", fontName="Helvetica-Bold", fontSize=10.5, leading=14,
            textColor=ACCENT, spaceBefore=8, spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=INK, leftIndent=10, bulletIndent=1, spaceAfter=3,
        ),
        "cell": ParagraphStyle(
            "cell", fontName="Helvetica", fontSize=9, leading=12.5,
            textColor=INK,
        ),
        "cellhead": ParagraphStyle(
            "cellhead", fontName="Helvetica-Bold", fontSize=9, leading=12.5,
            textColor=colors.white,
        ),
        "note": ParagraphStyle(
            "note", fontName="Helvetica-Oblique", fontSize=9, leading=13,
            textColor=MUTED, spaceBefore=4, spaceAfter=6,
        ),
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Helvetica-Bold", fontSize=30, leading=36,
            textColor=colors.white, alignment=TA_CENTER,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="Helvetica", fontSize=13, leading=18,
            textColor=colors.HexColor("#8b93a7"), alignment=TA_CENTER,
        ),
        "cover_kicker": ParagraphStyle(
            "cover_kicker", fontName="Helvetica-Bold", fontSize=11, leading=15,
            textColor=ACCENT, alignment=TA_CENTER,
        ),
        "cover_body": ParagraphStyle(
            "cover_body", fontName="Helvetica", fontSize=10.5, leading=16,
            textColor=INK, alignment=TA_CENTER,
        ),
        "cover_foot": ParagraphStyle(
            "cover_foot", fontName="Helvetica", fontSize=9, leading=13,
            textColor=MUTED, alignment=TA_CENTER,
        ),
    }


# ------------------------------------------------------------ page frames

def draw_cover(canvas, doc) -> None:
    """Dark hero band across the top of the cover page."""
    canvas.saveState()
    canvas.setFillColor(BAND)
    canvas.rect(0, PAGE_H - 118 * mm, PAGE_W, 118 * mm, stroke=0, fill=1)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 121 * mm, PAGE_W, 3 * mm, stroke=0, fill=1)
    canvas.restoreState()


def draw_content(canvas, doc) -> None:
    """Running header and footer on content pages."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, PAGE_H - 13 * mm, DOC_TITLE)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 13 * mm, f"Page {doc.page}")

    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, PAGE_H - 15 * mm, PAGE_W - MARGIN, PAGE_H - 15 * mm)
    canvas.line(MARGIN, 15 * mm, PAGE_W - MARGIN, 15 * mm)

    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 11 * mm, "Designed by Codecider Lab")
    canvas.drawRightString(PAGE_W - MARGIN, 11 * mm, "Released under the GNU AGPL-3.0")
    canvas.restoreState()


def build_doc(path: Path) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(path), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=22 * mm, bottomMargin=20 * mm,
        title=DOC_TITLE, author="Codecider Lab", subject=SUBTITLE,
    )
    frame_cover = Frame(MARGIN, 20 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 40 * mm,
                        id="cover")
    frame_body = Frame(MARGIN, 20 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 42 * mm,
                       id="body")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame_cover], onPage=draw_cover),
        PageTemplate(id="content", frames=[frame_body], onPage=draw_content),
    ])
    return doc


# ------------------------------------------------------------- helpers

def block(*flowables) -> KeepTogether:
    """Keep a heading and its table on one page, so no single row is orphaned."""
    out: list = []
    for f in flowables:
        out.extend(f if isinstance(f, list) else [f])
    return KeepTogether(out)


def table(styles, rows: list[list[str]], widths: list[float]) -> Table:
    """Build a zebra-striped table whose first row is a header."""
    data = [[Paragraph(c, styles["cellhead"]) for c in rows[0]]]
    data += [[Paragraph(c, styles["cell"]) for c in row] for row in rows[1:]]

    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
    ]
    for i in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    t.setStyle(TableStyle(style))
    return t


def code(text: str) -> Preformatted:
    style = ParagraphStyle(
        "code", fontName="Courier", fontSize=8.5, leading=12,
        textColor=INK, backColor=ZEBRA, borderColor=RULE, borderWidth=0.5,
        borderPadding=7, spaceBefore=4, spaceAfter=8,
    )
    return Preformatted(text, style)


def bullets(styles, items: list[str]) -> list:
    return [Paragraph(f"•&nbsp;&nbsp;{i}", styles["bullet"]) for i in items]


def screenshot(width: float) -> list:
    """The app screenshot, scaled to ``width``. Empty if the asset is missing."""
    path = ROOT / "assets" / "screenshot.png"
    if not path.exists():
        return []
    reader = ImageReader(str(path))
    src_w, src_h = reader.getSize()
    return [Image(str(path), width=width, height=width * src_h / src_w)]


# ---------------------------------------------------------------- content

def cover(styles) -> list:
    return [
        Spacer(1, 26 * mm),
        Paragraph(TITLE, styles["cover_title"]),
        Spacer(1, 5 * mm),
        Paragraph(SUBTITLE, styles["cover_sub"]),
        Spacer(1, 12 * mm),
        Paragraph("USER MANUAL", styles["cover_kicker"]),
        Spacer(1, 48 * mm),
        Paragraph(
            "Sort a folder of photos into dated folders automatically, using the "
            "shot time recorded in each photo's EXIF data. Choose year, month, or "
            "day; photos without a shot time are set aside in <b>others</b>.",
            styles["cover_body"],
        ),
        Spacer(1, 10 * mm),
        Paragraph(
            "Open-source&nbsp;&nbsp;·&nbsp;&nbsp;Windows&nbsp;&nbsp;·"
            "&nbsp;&nbsp;No models, no downloads&nbsp;&nbsp;·"
            "&nbsp;&nbsp;Originals never modified",
            styles["cover_foot"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Designed by Codecider Lab", styles["cover_foot"]),
    ]


def section_overview(styles) -> list:
    w = PAGE_W - 2 * MARGIN
    return [
        Paragraph("1. Overview", styles["h1"]),
        Paragraph(
            "Photo Time Classifier is a desktop application that scans a folder "
            "of photos, reads the shot time recorded in each photo's EXIF metadata, "
            "and copies the photos into folders named after that time. You pick one "
            "grouping - year, month, or day - and the folders are created for you.",
            styles["body"],
        ),
        Paragraph(
            "The shot time is the moment the shutter actually fired, which the camera "
            "or phone writes into the file. It is not the file's created or modified "
            "date, so copying, syncing, or re-downloading photos does not change how "
            "they are sorted.",
            styles["body"],
        ),
        Paragraph("Key features", styles["h2"]),
        *bullets(styles, [
            "Sorts by EXIF shot time into <b>year</b>, <b>month</b>, or <b>day</b> folders.",
            "Photos with no shot time go to <b>others</b> rather than being dropped.",
            "Reads JPEG, HEIC/HEIF (iPhone), TIFF, PNG, BMP, and WebP files.",
            "Photos are <b>copied, never moved</b> - the source folder is left untouched.",
            "Same-named photos are kept side by side as <b>name_1.jpg</b>, <b>name_2.jpg</b>.",
            "Damaged photos - partially damaged or fully corrupt - are set aside in <b>Damaged</b>.",
            "No machine-learning models and no first-run downloads - it starts instantly.",
            "Responsive dark-themed interface; the app never freezes during processing.",
        ]),
        Paragraph("2. Installation &amp; First Run", styles["h1"]),
        Paragraph("Requirements", styles["h2"]),
        *bullets(styles, [
            "Windows 10/11, Python 3.10 or newer.",
            "No GPU and no internet connection are required.",
        ]),
        Paragraph("Setup", styles["h2"]),
        Paragraph(
            "Double-click <b>run.bat</b>. On the first run it automatically creates a "
            "virtual environment, installs the dependencies, and launches the app. "
            "Later runs start the app directly.",
            styles["body"],
        ),
        Paragraph(
            "If you downloaded a pre-built release instead, run "
            "<b>PhotoTimeClassifier.exe</b> - no Python needed.",
            styles["body"],
        ),
        Paragraph("Running the tests (optional)", styles["h2"]),
        Paragraph("Double-click <b>test.bat</b> to run the unit test suite.", styles["body"]),
    ]


def section_usage(styles) -> list:
    w = PAGE_W - 2 * MARGIN
    return [
        block(
            Paragraph("3. The Interface", styles["h1"]),
            Paragraph(
                "The window has two columns. The left column holds the settings and "
                "controls; the right column shows the live log.",
                styles["body"],
            ),
            screenshot(w * 0.92),
            Spacer(1, 5 * mm),
            table(styles, [
                ["Area", "Purpose"],
                ["Folders", "Choose the <b>Source</b> folder (input) and "
                            "<b>Destination</b> folder (output)."],
                ["Scan", "<b>Search subfolders</b> - also collect photos from nested "
                         "folders."],
                ["Classification", "Pick one grouping: <b>Year</b>, <b>Month</b>, or "
                                   "<b>Day</b>."],
                ["Start / Stop", "Begin or safely halt processing."],
                ["Progress bar", "Shows how many photos have been processed."],
                ["Log", "Per-photo results and the final summary."],
            ], [w * 0.22, w * 0.78]),
        ),
        block(
            Paragraph("4. Step-by-Step Usage", styles["h1"]),
            table(styles, [
                ["Step", "Action"],
                ["1", "Click <b>Browse</b> next to <b>Source</b> and select the folder "
                      "of photos to scan."],
                ["2", "Click <b>Browse</b> next to <b>Destination</b> and select where "
                      "results should be saved (must differ from Source)."],
                ["3", "Leave <b>Search subfolders</b> on to include nested folders."],
                ["4", "Choose <b>Year</b>, <b>Month</b>, or <b>Day</b>. Only one can be "
                      "selected at a time."],
                ["5", "Click <b>Start</b>. Watch progress in the log; click <b>Stop</b> "
                      "to halt at any time."],
                ["6", "When finished, the summary line reports totals, and the dated "
                      "folders are in your Destination folder."],
            ], [w * 0.09, w * 0.91]),
        ),
    ]


def section_options(styles) -> list:
    w = PAGE_W - 2 * MARGIN
    return [
        Paragraph("5. Classification Options", styles["h1"]),
        Paragraph(
            "Exactly one option is active per run - they are radio buttons, not "
            "checkboxes. The option decides how finely the photos are grouped and how "
            "the destination folders are named.",
            styles["body"],
        ),
        table(styles, [
            ["Option", "Folder name", "Example", "Best for"],
            ["Year", "YYYY", "2026", "Long archives you want in broad buckets."],
            ["Month", "YYYY-MM", "2026-07", "A good balance for most photo libraries."],
            ["Day", "YYYY-MM-DD", "2026-07-16", "Trips and events, where each day matters."],
        ], [w * 0.14, w * 0.20, w * 0.22, w * 0.44]),
        Paragraph(
            "Tip: run the same source folder twice with different options to compare - "
            "your originals are only ever copied, never changed.",
            styles["note"],
        ),
        block(
            Paragraph("6. Output Folder Structure", styles["h1"]),
            Paragraph(
                "Folders are created under your Destination folder as they are needed. "
                "Photos land directly inside their dated folder; the source subfolder "
                "layout is not recreated underneath it.",
                styles["body"],
            ),
            table(styles, [
                ["Folder", "Contents"],
                ["2026 / 2026-07 / 2026-07-16", "Photos whose EXIF shot time falls in "
                                                "that year, month, or day."],
                ["others", "Photos with no EXIF shot time (screenshots, scans, most "
                           "PNGs, stripped metadata)."],
                ["Damaged", "Photos that are damaged - either partially (truncated or "
                            "broken pixel data) or too corrupt to open at all."],
            ], [w * 0.32, w * 0.68]),
        ),
        Paragraph("Example, with <b>Day</b> selected:", styles["body"]),
        code(
            "Destination/\n"
            "  2025-12-24/  xmas.jpg\n"
            "  2026-01-01/  newyear.jpg\n"
            "  2026-07-16/  beach.jpg\n"
            "               beach_1.jpg      <- same name, kept side by side\n"
            "               sunset.jpg\n"
            "  others/      screenshot.png\n"
            "  Damaged/     truncated.jpg\n"
            "               broken.jpg"
        ),
    ]


def section_details(styles) -> list:
    w = PAGE_W - 2 * MARGIN
    return [
        Paragraph("7. Photos Without a Shot Time", styles["h1"]),
        Paragraph(
            "Not every image carries EXIF data. Screenshots, scans, edited exports, "
            "downloaded images, and most PNG or BMP files have no shot time at all, "
            "and some apps strip the metadata when photos are shared. These photos are "
            "copied to <b>others</b> so nothing is silently lost, and the log shows "
            "<b>No shot time</b> for each one.",
            styles["body"],
        ),
        block(
            Paragraph("Three EXIF tags are checked, in this order:", styles["body"]),
            table(styles, [
                ["Tag", "Meaning"],
                ["DateTimeOriginal", "When the shutter fired. Preferred."],
                ["DateTimeDigitized", "When the image was digitized (e.g. a scan)."],
                ["DateTime", "Last change recorded by the camera or software."],
            ], [w * 0.28, w * 0.72]),
        ),
        block(
            Paragraph("8. Damaged &amp; Corrupt Images", styles["h1"]),
            Paragraph("Every image is checked before processing:", styles["body"]),
            table(styles, [
                ["Condition", "Handling"],
                ["OK", "Header and pixels decode fully &#8594; sorted by shot time."],
                ["Partially damaged", "Opens but pixel data is truncated/broken &#8594; "
                                      "copied to <b>Damaged</b>."],
                ["Fully corrupt", "Cannot be opened at all &#8594; copied to "
                                  "<b>Damaged</b>."],
            ], [w * 0.24, w * 0.76]),
            Paragraph(
                "Damaged photos are separated into <b>Damaged</b> so they never mix "
                "into the dated folders. Nothing is dropped: even a file too corrupt "
                "to open is copied there, so you can inspect or recover it yourself.",
                styles["body"],
            ),
        ),
        block(
            Paragraph("9. Supported Formats", styles["h1"]),
            code(".jpg  .jpeg  .png  .bmp  .webp  .tif  .tiff  .heic  .heif"),
            Paragraph(
                "EXIF shot time is most commonly present in JPEG, HEIC, and TIFF files "
                "- the formats cameras and phones produce. Formats that carry no EXIF "
                "(typically PNG and BMP) are sorted into <b>others</b>.",
                styles["body"],
            ),
        ),
        Paragraph("10. Troubleshooting", styles["h1"]),
        table(styles, [
            ["Symptom", "What to do"],
            ["\"Python not found\"", "Install Python 3.10+ and add it to PATH, then "
                                     "rerun run.bat."],
            ["No images found", "Check the Source folder and enable <b>Search "
                                "subfolders</b>."],
            ["Everything went to <b>others</b>", "Those files carry no EXIF shot time - "
                                                 "common for screenshots, scans, and "
                                                 "PNGs, or if an app stripped the "
                                                 "metadata when sharing."],
            ["Dates look wrong", "The camera clock was wrong when the photo was taken; "
                                 "the app files photos exactly as the camera recorded "
                                 "them."],
            ["A photo is missing", "Check the <b>Damaged</b> folder - damaged files are "
                                   "set aside there instead of the dated folders."],
            ["Two photos, one name", "Both are kept: the second becomes "
                                     "<b>name_1.jpg</b>. Nothing is overwritten."],
        ], [w * 0.26, w * 0.74]),
    ]


def section_cli(styles) -> list:
    w = PAGE_W - 2 * MARGIN
    return [
        Paragraph("11. Command-Line Interface", styles["h1"]),
        Paragraph(
            "The same pipeline is available without the GUI, for scripting and batch "
            "jobs. On Windows you can use <b>cli.bat</b> in place of "
            "<b>python cli.py</b>.",
            styles["body"],
        ),
        code(
            "python cli.py SOURCE DESTINATION [options]\n\n"
            "python cli.py ./photos ./sorted            # sort by day (default)\n"
            "python cli.py ./photos ./sorted --year     # sort into 2026/\n"
            "python cli.py ./photos ./sorted --month    # sort into 2026-07/\n"
            "python cli.py ./photos ./sorted --day --no-recursive -q"
        ),
        table(styles, [
            ["Option", "Description"],
            ["--year", "Sort into year folders (2026)."],
            ["--month", "Sort into year-month folders (2026-07)."],
            ["--day", "Sort into year-month-day folders (2026-07-16). Default."],
            ["--no-recursive", "Do not scan subfolders."],
            ["-q, --quiet", "Show a progress bar instead of per-image lines."],
        ], [w * 0.24, w * 0.76]),
        Paragraph(
            "<b>--year</b>, <b>--month</b>, and <b>--day</b> are mutually exclusive, "
            "matching the radio buttons in the app.",
            styles["body"],
        ),
        Paragraph(
            "Press <b>Ctrl+C</b> to stop gracefully; a summary is still printed. The "
            "exit code is <b>0</b> on success and <b>1</b> on a fatal error.",
            styles["body"],
        ),
        Spacer(1, 8 * mm),
        Paragraph(
            "Photo Time Classifier is open-source software, released under the GNU "
            "AGPL-3.0. It uses PyQt5 (GPL-3.0), Pillow (HPND), and pi-heif "
            "(Apache-2.0). No machine-learning models are used and nothing is "
            "downloaded at first run. Designed by Codecider Lab.",
            styles["note"],
        ),
    ]


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "USER_MANUAL.pdf"
    styles = build_styles()

    story: list = [
        *cover(styles),
        NextPageTemplate("content"),
        PageBreak(),
        *section_overview(styles),
        PageBreak(),
        *section_usage(styles),
        PageBreak(),
        *section_options(styles),
        PageBreak(),
        *section_details(styles),
        PageBreak(),
        *section_cli(styles),
    ]

    build_doc(target).build(story)
    print(f"Wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
