from driver import epd7in5b
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageChops
import os, sys
import logging
import tempfile


class InfoWindow:
    def __init__(self, options, colour):
        self.epd = epd7in5b.EPD()
        self.epd.init()
        self.width = 880
        self.height = 528
        self.image = Image.new('L', (880, 528), 255)
        self.draw = ImageDraw.Draw(self.image)
        self.fonts = {}
        self.colour = colour
        self.initFonts()
        self.tmpImagePath = os.path.join(tempfile.gettempdir(), colour+".png")
        self.timeformat = options['timeformat']

    def getCWD(self):
        path = os.path.dirname(os.path.realpath(sys.argv[0]))
        return path

    def getImage(self):
        return self.image

    def getDraw(self):
        return self.draw

    def getEpd(self):
        return self.epd

    def line(self, left_1, top_1, left_2, top_2, fill=0, width=1):
        self.draw.line((left_1, top_1, left_2, top_2), fill=fill)

    def rectangle(self, tl, tr, bl, br, fill=0):
        self.draw.rectangle(((tl, tr), (bl, br)), fill=fill)

    def text(self, left, top, text, font, fill=0):
        font = self.fonts[font]
        self.draw.text((left, top), text, font=font, fill=fill)
        return self.draw.textsize(text, font=font)

    def textwidth(self, text, font):
        font = self.fonts[font]
        ascent, descent = font.getmetrics()
        text_width = font.getmask(text).getbbox()[2]
        text_height = font.getmask(text).getbbox()[3] + descent
        text_width = (text_width/2)
        return text_width

    def rotate(self, angle):
        self.image.rotate(angle)

    # def chord(self, x, y, xx, yy, xxx, yyy, fill):
    #     self.draw.chord((x, y, xx, yy), xxx, yyy, fill)

    def bitmap(self, x, y, image_path):
        bitmap = Image.open(self.getCWD()+"/icons/"+image_path)
        # self.image.paste((0, 0), (x, y), 'black', bitmap)
        self.draw.bitmap((x, y), bitmap)



    def getFont(self, font_name):
        return self.fonts[font_name]

    def initFonts(self):
        roboto = self.getCWD()+"/fonts/roboto/Roboto-"
        self.fonts = {

            'robotoBlack24': ImageFont.truetype(roboto+"Black.ttf", 24),
            'robotoBlack18': ImageFont.truetype(roboto+"Black.ttf", 18),
            'robotoRegular18': ImageFont.truetype(roboto+"Regular.ttf", 18),
            'robotoRegular14': ImageFont.truetype(roboto+"Regular.ttf", 14),
            'robotoBlack48': ImageFont.truetype(roboto+"Black.ttf", 48),
            'robotoBlack36': ImageFont.truetype(roboto+"Black.ttf", 36)
        }

    def truncate(self, string, font, max_size):
        num_chars = len(string)
        for char in string:
            (np_x, np_y) = self.getFont(font).getsize(string)
            if np_x >= max_size:
                string = string[:-1]

            if np_x <= max_size:
                return string

        return string
    
    def align(self, string, font, max_size):
        spacechar = string.find(" ")
        num_chars = len(string)
        for char in string:
            (np_x, np_y) = self.getFont(font).getsize(string)
            if np_x < max_size:
                oldstring = string
                string = string[0:spacechar] + " " + string [:-1]

            if np_x > max_size:
                return oldstring

        return oldstring

    def display(self, angle):

        Limage = Image.new('1', (880, 528), 255)  # 255: clear the frame
        self.image = self.image.rotate(angle)

        new_image_found = True
        if os.path.exists(self.tmpImagePath):
            old_image = Image.open(self.tmpImagePath)
            diff = ImageChops.difference(self.image, old_image)
            if not diff.getbbox():
                new_image_found = False

        if new_image_found:
            logging.info("New information in the image detected. Updating the screen.")
            self.image.save(self.tmpImagePath)
        else:
            logging.info("No new information found. Not updating the screen.")
