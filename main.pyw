#!/usr/bin/python3

import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps

from webbrowser import Error as wb_error
from webbrowser import open as wb_open
from PyQt5 import QtWidgets, QtCore, QtGui

from protractor_ui import Ui_MainWindow

class ProtractorGen(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(ProtractorGen, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.button_generate.clicked.connect(self.generate_protractor)
        self.setWindowTitle("Protractor Generator")

    def generate_protractor(self):
        pot_degrees = self.spinbox_degrees.value()
        dead_zone = (pot_degrees / 2) * ((self.spinbox_deadzone.value() / 2) / 100)
        pot_degrees = ((pot_degrees / 2) - dead_zone) * 2
        resist_ratio = self.spinbox_resistance.value() / pot_degrees
        graph_rot_offset = -1 * ((360 - self.spinbox_degrees.value()) / 2)
        temp_range = range(40, 24, -1)
        res_w, res_h = 5000, 5000

        print(pot_degrees)

        img = Image.new(mode = "RGB", size = (res_w, res_h))
        img1 = ImageDraw.Draw(img)

        if sys.platform == 'linux':
            font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 90)
        elif sys.platform == 'darwin':
            font = ImageFont.truetype("/System/Library/Fonts/Keyboard.ttf", 90)
        elif sys.platform == 'win32':
            font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 90)
        else:
            font = ImageFont.load_default()

        for i in range(0, self.spinbox_degrees.value()):
            angle = (360 - i) + graph_rot_offset
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            x_start = x * (res_w / 2.2)
            y_start = y * (res_h / 2.2)
            x_end = x * res_w / 2
            y_end = y * res_h / 2
            segment = [((res_w / 2) + x_start, (res_h // 2) + y_start), ((res_w // 2) + x_end, (res_h // 2) + y_end)]
            img1.line(segment, width = 10)

        
        for i in temp_range:
            ang = self.get_angle_from_celsius(i, resist_ratio) - dead_zone
            if(ang < 0):
                continue
            angle = (360 - ang) + graph_rot_offset
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            x_start = 0
            y_start = 0
            x_end = x * res_w / 2
            y_end = y * res_h / 2
            segment = [((res_w / 2) + x_start, (res_h // 2) + y_start), ((res_w // 2) + x_end, (res_h // 2) + y_end)]
            img1.line(segment, width = 10)

            # add labels
            img_text = Image.new(mode = "RGBA", size = (200, 200), color = (0, 255, 0, 0))
            imgt = ImageDraw.Draw(img_text)
            imgt.text((50, 50), text = str(i), font = font, align = 'center')
            tr = img_text.size
            angle = (360 - ang) + graph_rot_offset + 2
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            position = (
                int(((res_w // 2) + (x * (res_w // 2.4))) - (tr[0] / 2)),
                int(((res_h // 2) + (y * (res_h // 2.4))) - (tr[1] / 2))
            )
            img.paste(img_text, position, img_text)

        img = img.resize((res_w // 4, res_h // 4), resample = Image.LANCZOS)

        if(not self.checkbox_invert.isChecked()):
            img = ImageOps.invert(img)

        img.show()

    def get_angle_from_celsius(self, temp: int, resist_ratio: float) -> int:
        resistance = (-0.0296 * (temp ** 3)) + (4.5449 * (temp ** 2)) + (-270.1504 * temp) + 6628.8089
        resistance = resistance - 1200         # remove minimum resistance expected at lowest setting for calibration
        return(self.spinbox_degrees.value() - round(resistance / resist_ratio))



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_app = ProtractorGen()
    main_app.show()
    ret = app.exec_()       # main loop call
