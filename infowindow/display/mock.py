from __future__ import annotations

import logging
import subprocess

from PIL import Image, ImageOps

from infowindow.utils.paths import cache_path

log = logging.getLogger(__name__)

_PREVIEW_PATH = cache_path("InfoWindowPreview.png")


class MockEPD:
    """Local-development stand-in for the Waveshare e-ink driver.

    Composites the two 1-bit layers into a colour preview PNG and opens
    it with the default image viewer so the result is immediately visible.
    """

    def init(self) -> None:
        log.info("MockEPD: init (no-op)")

    def display(self, black_image: Image.Image, red_image: Image.Image) -> None:
        width, height = black_image.size

        preview = Image.new("RGB", (width, height), "white")

        # Black layer first: where black_image pixel = 0 (has ink), paint black
        black_layer = Image.new("RGB", (width, height), "black")
        black_mask  = ImageOps.invert(black_image.convert("L"))
        preview.paste(black_layer, mask=black_mask)

        # Red layer on top: where red_image pixel = 0 (has ink), paint red.
        # Red wins over black — matches Waveshare 7.5" B V2 hardware behaviour.
        red_layer = Image.new("RGB", (width, height), "red")
        red_mask  = ImageOps.invert(red_image.convert("L"))
        preview.paste(red_layer, mask=red_mask)

        preview.save(_PREVIEW_PATH)
        log.info("MockEPD: preview saved to %s", _PREVIEW_PATH)

        try:
            subprocess.Popen(["xdg-open", str(_PREVIEW_PATH)])
        except FileNotFoundError:
            # xdg-open not available (e.g. macOS); fall back to PIL viewer
            preview.show()

    def sleep(self) -> None:
        log.info("MockEPD: sleep (no-op)")

    def clear_cache(self) -> None:
        """No cache to clear on the mock."""
