#!/usr/bin/env python2

import logging
import os
from driver import epd7in5b
from PIL import Image

# Setup Logging -  change to logging.DEBUG if you are having issues.
logging.basicConfig(level=logging.INFO)
logging.info("Screen saver starting")


def main():
    epd = epd7in5b.EPD()
    epd.init()

    black = Image.open(os.path.join("resources", "black.png"))
    red = Image.open(os.path.join("resources", "red.png"))
    white = Image.open(os.path.join("resources", "white.png"))
    epd.display(epd.getbuffer(black),epd.getbuffer(white))
    logging.info("Display black")
    epd.display(epd.getbuffer(white),epd.getbuffer(black))
    logging.info("Display red")
    epd.display(epd.getbuffer(white),epd.getbuffer(white))
    logging.info("Display white")
      
    epd.sleep()
    logging.info("Screen saver finished")

    os.remove(os.path.join(tempfile.gettempdir(), "black.png"))

if __name__ == '__main__':
    main()
