#!/usr/bin/env python3

import logging
import os
from PIL import Image

from driver import epd7in5b_V2

# Setup Logging -  change to logging.DEBUG if you are having issues.
logging.basicConfig(level=logging.INFO)
logging.info("Screen saver starting")

def display_image(epd, black_fill, red_fill):
    width = 800
    height = 480

    # Create 1-bit monochrome images like the working infowindow.py
    black_image = Image.new('1', (width, height), black_fill)
    red_image = Image.new('1', (width, height), red_fill)

    epd.display(epd.getbuffer(black_image), epd.getbuffer(red_image))


def main():
    epd = epd7in5b_V2.EPD()
    epd.init()

    logging.info("Display black screen")
    display_image(epd, black_fill=0, red_fill=1)

    logging.info("Display red screen")
    display_image(epd, black_fill=1, red_fill=0)

    logging.info("Display white screen")
    epd.Clear()
    epd.sleep()
    logging.info("Screen saver finished")


if __name__ == '__main__':
    main()
