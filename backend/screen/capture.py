"""Screen capture module using mss for fast screenshot capture."""

import base64
import io
import logging

import mss
from PIL import Image

logger = logging.getLogger(__name__)


def capture_screen(monitor_index: int = 0, max_dimension: int = 1920) -> str:
    """Capture the screen and return a base64-encoded JPEG image.

    Args:
        monitor_index: Which monitor to capture (0 = all monitors combined).
        max_dimension: Resize if any dimension exceeds this (saves tokens).

    Returns:
        Base64-encoded JPEG string suitable for vision LLM APIs.
    """
    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index >= len(monitors):
            monitor_index = 0

        screenshot = sct.grab(monitors[monitor_index])
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    # Resize if too large (saves LLM tokens/cost)
    w, h = img.size
    if max(w, h) > max_dimension:
        scale = max_dimension / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Encode as JPEG
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("utf-8")
