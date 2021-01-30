#!/usr/bin/env python2

import logging
import os
import tempfile
from driver import epd7in5b
from PIL import Image

# Setup Logging -  change to logging.DEBUG if you are having issues.
logging.basicConfig(level=logging.INFO)
logging.info("Screen saver starting")


def main():
    epd = epd7in5b.EPD()
    epd.init()

    black = Image.open(os.path.join(os.path.dirname(sys.argv[0]), "resources", "black.png"))
    red = Image.open(os.path.join(os.path.dirname(sys.argv[0]),"resources", "red.png"))
    white = Image.open(os.path.join(os.path.dirname(sys.argv[0]),"resources", "white.png"))
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
