# Third-Party Notices

Photo Time Classifier is licensed under **AGPL-3.0** (see [LICENSE](LICENSE)).
It uses the third-party components listed below, each under its own license.

## Why AGPL-3.0

The GUI uses **PyQt5**, which is licensed under **GPL-3.0**: a strong copyleft
license requiring any distributed work that includes it to be released under
GPL-3.0 (or a compatible license) with source available. This project as a
whole is released under **AGPL-3.0**, which is compatible with GPL-3.0.

> Earlier versions bundled Ultralytics YOLO (AGPL-3.0), which originally forced
> the AGPL-3.0 choice. That dependency has been removed, so AGPL-3.0 is now a
> deliberate choice rather than a requirement; PyQt5's GPL-3.0 remains the
> binding copyleft constraint.

## Dependency licenses

### Runtime (`requirements.txt`)

| Component | License | Notes |
|-----------|---------|-------|
| PyQt5 | GPL-3.0 | GUI framework (commercial license also available from Riverbank) |
| Pillow | MIT-CMU | Image decoding and EXIF reading |
| pi-heif | BSD-3-Clause | HEIC/HEIF (iPhone photo) support. The PyPI **binary wheels are LGPL-3.0** as a whole, because of the bundled libraries below. |
| libheif | LGPL-3.0 | Bundled in the `pi-heif` wheel |
| libde265 | LGPL-3.0 | HEVC decoder, bundled in the `pi-heif` wheel |

### Development and build only (`requirements-dev.txt`)

These are not distributed with the application and do not affect its license.

| Component | License | Notes |
|-----------|---------|-------|
| pytest | MIT | Test runner |
| ReportLab | BSD-3-Clause | Generates `USER_MANUAL.pdf` |
| PyInstaller | GPL-2.0-or-later, with the bootloader exception | Builds the Windows executables. The exception explicitly permits distributing the resulting executable under any license. |

No machine-learning models or model weights are used, and nothing is
downloaded at first run.

## Binary releases

The Windows executables attached to GitHub Releases are built with PyInstaller
and bundle PyQt5 (GPL-3.0) together with the LGPL-3.0 libraries listed above.
Distributing them under AGPL-3.0 satisfies both: the complete corresponding
source is published in this repository, and `build_exe.py` reproduces the
executables from it, which is what LGPL-3.0 requires for the bundled libraries.

## Commercial use

Because of PyQt5's GPL-3.0 terms, this project **is not suitable for
proprietary or commercial distribution as-is**. To make it commercial-ready you
would need to obtain a Riverbank commercial license for PyQt5 or migrate the
GUI to an LGPL alternative such as PySide6, and relicense this project's own
code accordingly.

This file is informational and is not legal advice.
