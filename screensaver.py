#!/usr/bin/env python3
"""InfoWindow screensaver — cycles black/red/white screens to prevent ghosting."""
from __future__ import annotations

import logging
import random

from PIL import Image

from infowindow.display import get_display

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def main() -> None:
    log.info("Screen saver starting")
    device = get_display()
    device.init()

    colors = ["black", "red", "white"]
    random.shuffle(colors)

    for color in colors:
        log.info("Displaying %s screen", color)
        width, height = 800, 480
        if color == "black":
            black = Image.new("1", (width, height), 0)
            red   = Image.new("1", (width, height), 1)
            device.display(black, red)
        elif color == "red":
            black = Image.new("1", (width, height), 1)
            red   = Image.new("1", (width, height), 0)
            device.display(black, red)
        else:
            if hasattr(device, "clear"):
                device.clear()
            else:
                white = Image.new("1", (width, height), 1)
                device.display(white, white)

    log.info("Sleeping display")
    device.sleep()

    # Remove cached images so infowindow forces a full redraw next run.
    if hasattr(device, "clear_cache"):
        device.clear_cache()

    log.info("Screen saver finished")


if __name__ == "__main__":
    main()
