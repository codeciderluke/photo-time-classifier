"""Image inspection package.

Provides pure image-inspection utilities decoupled from the GUI layer. Has no
dependency on GUI frameworks like PyQt5, so it can be reused in CLI, batch,
server API, and test environments.
"""

from .image_integrity import CORRUPT, OK, PARTIAL, inspect_image

__all__ = [
    "inspect_image",
    "OK",
    "PARTIAL",
    "CORRUPT",
]
