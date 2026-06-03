from __future__ import annotations

import logging

from PIL import Image, ImageChops

from infowindow.utils.paths import cache_path

log = logging.getLogger(__name__)

# This import intentionally lives at module level so that ImportError
# propagates to get_display() in __init__.py and triggers the mock fallback.
from driver import epd7in5b_V2  # noqa: E402


class RealEPD:
    """Thin wrapper around the Waveshare epd7in5b_V2 driver.

    Owns change-detection so the display is only refreshed when pixel
    content actually differs from the previously saved images.
    """

    def __init__(self) -> None:
        self._epd = epd7in5b_V2.EPD()
        self._epd.init()
        self._cache_black = cache_path("InfoWindowBlack.png")
        self._cache_red   = cache_path("InfoWindowRed.png")
        log.info("Image cache: %s, %s", self._cache_black, self._cache_red)

    def display(self, black_image: Image.Image, red_image: Image.Image) -> None:
        changed = False
        for img, path, name in (
            (red_image,   self._cache_red,   "red"),
            (black_image, self._cache_black, "black"),
        ):
            if path.exists():
                diff = ImageChops.difference(
                    img.convert("L"),
                    Image.open(path).convert("L"),
                )
                bbox = diff.getbbox()
                if bbox:
                    log.info("%s layer changed at %s", name, bbox)
                    changed = True
            else:
                log.info("No previous %s image found, treating as new.", name)
                changed = True

        if changed:
            log.info("New information detected. Updating the screen.")
            black_image.save(self._cache_black)
            red_image.save(self._cache_red)
            self._epd.display(
                self._epd.getbuffer(black_image),
                self._epd.getbuffer(red_image),
            )
        else:
            log.info("No new information found. Not updating the screen.")

    def sleep(self) -> None:
        self._epd.sleep()

    def init(self) -> None:
        pass  # already called in __init__

    def clear(self) -> None:
        self._epd.Clear()

    def clear_cache(self) -> None:
        """Delete the cached comparison images (called by screensaver)."""
        for path in (self._cache_black, self._cache_red):
            if path.exists():
                path.unlink()
                log.info("Removed cached image: %s", path)
