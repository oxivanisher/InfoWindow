from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from infowindow.utils.paths import FONTS_DIR, ICONS_DIR

log = logging.getLogger(__name__)

_FONT_VARIANTS: dict[str, tuple[str, int]] = {
    "robotoBlack14": ("Black", 14),
    "robotoBlack18": ("Black", 18),
    "robotoBold22":  ("Bold",  22),
    "robotoBlack22": ("Black", 22),
    "robotoBlack24": ("Black", 24),
    "robotoBlack54": ("Black", 54),
}


class Canvas:
    """Pure-PIL drawing surface for the two-layer (black + red) e-ink display."""

    WIDTH = 800
    HEIGHT = 480

    def __init__(self, options: dict) -> None:
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.black_image = Image.new("1", (self.WIDTH, self.HEIGHT), 1)
        self.red_image   = Image.new("1", (self.WIDTH, self.HEIGHT), 1)
        self.black_draw  = ImageDraw.Draw(self.black_image)
        self.red_draw    = ImageDraw.Draw(self.red_image)
        self._fonts: dict[str, ImageFont.FreeTypeFont] = {}
        self._init_fonts()
        self.timeformat: str = options["timeformat"]

    # ------------------------------------------------------------------
    # Drawing primitives
    # ------------------------------------------------------------------

    def line(self, x1: int, y1: int, x2: int, y2: int, fill: str) -> None:
        coords = (x1, y1, x2, y2)
        if fill == "black":
            self.black_draw.line(coords, fill=0)
        elif fill == "red":
            self.red_draw.line(coords, fill=0)
        elif fill == "white":
            self.black_draw.line(coords, fill=1)
            self.red_draw.line(coords, fill=1)

    def rectangle(self, tl: float, tr: float, bl: float, br: float, fill: str) -> None:
        box = ((tl, tr), (bl, br))
        if fill == "black":
            self.black_draw.rectangle(box, fill=0)
        elif fill == "red":
            self.red_draw.rectangle(box, fill=0)
        elif fill == "white":
            self.black_draw.rectangle(box, fill=1)
            self.red_draw.rectangle(box, fill=1)

    def text(self, x: float, y: float, content: str, font: str, fill: str) -> None:
        fnt = self._fonts[font]
        pos = (x, y)
        if fill == "black":
            self.black_draw.text(pos, content, font=fnt, fill=0)
        elif fill == "red":
            self.black_draw.text(pos, content, font=fnt, fill=0)
            self.red_draw.text(pos, content, font=fnt, fill=0)
        elif fill == "white":
            self.black_draw.text(pos, content, font=fnt, fill=1)
            self.red_draw.text(pos, content, font=fnt, fill=1)

    def bitmap(self, x: int, y: int, image_name: str) -> None:
        bmp = Image.open(ICONS_DIR / image_name)
        self.black_draw.bitmap((x, y), bmp, fill=0)

    # ------------------------------------------------------------------
    # Font helpers
    # ------------------------------------------------------------------

    def get_font(self, name: str) -> ImageFont.FreeTypeFont:
        return self._fonts[name]

    def truncate(self, text: str, font: str, max_width: int) -> str:
        fnt = self._fonts[font]
        while fnt.getlength(text) > max_width and text:
            text = text[:-1]
        return text

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def render(self, angle: int) -> tuple[Image.Image, Image.Image]:
        """Return (black_image, red_image) rotated by *angle* degrees."""
        return self.black_image.rotate(angle), self.red_image.rotate(angle)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _init_fonts(self) -> None:
        for name, (variant, size) in _FONT_VARIANTS.items():
            path = FONTS_DIR / f"Roboto-{variant}.ttf"
            self._fonts[name] = ImageFont.truetype(str(path), size)
