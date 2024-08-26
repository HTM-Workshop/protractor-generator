#!/usr/bin/python3
#
#   WARNING: This program and the Temp Sim board are NOT FOR MEDICAL USE!
#
#           Protractor Generator
#   Written by Kevin Williams - 2024
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

VERSION = "v1.0.0"
DEBUG = False

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
        self.setWindowTitle(f"Protractor Generator - {VERSION}")
        self._usable_degrees = 0

    def generate_protractor(self):

        # total mechanical degrees as per the datasheet
        pot_degrees = self.spinbox_degrees.value()

        # calculate the deadzone degrees based on the datasheet's deadzone range
        self.dead_zone = pot_degrees * (self.spinbox_deadzone.value() / 100)

        # usable degrees (mechanical degrees minus deadzone)
        #   This is the final range used for the rest of the program.
        self.usable_degrees = pot_degrees - self.dead_zone

        # change in resistance per angular degree (dR/dA)
        self.r_per_degree = self.spinbox_resistance.value() / self.usable_degrees

        # graph rotation amount
        graph_rot_offset = -1 * ((360 - self.spinbox_degrees.value()) / 2)

        # graph resolution
        res_w, res_h = 5000, 5000

        # temp range to plot
        temp_range = range(40, 1, -1)

        if DEBUG:
            # debug
            print(f"Usable degrees: {self.usable_degrees}")
            print(f"Deadzone: {self.dead_zone}")
            print(f"Degrees in celsius per angular degree: {self.r_per_degree}")
            print(f"Rot: {graph_rot_offset}")

        # open new image and font
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

        
        # Draw the outer degree ring.
        for i in range(0, self.spinbox_degrees.value()):
            angle = ((360 - i) + graph_rot_offset)
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            x_start = x * (res_w / 2.2)
            y_start = y * (res_h / 2.2)
            x_end = x * res_w / 2
            y_end = y * res_h / 2
            segment = [((res_w / 2) + x_start, (res_h // 2) + y_start), ((res_w // 2) + x_end, (res_h // 2) + y_end)]
            img1.line(segment, width = 10)

        
        # draw the major temperature divisions
        for i in temp_range:
            ang = self.get_angle_from_celsius(i, self.r_per_degree, self.dead_zone)
            if(ang < 0):
                break
            angle = ((360 - ang) + graph_rot_offset) - self.dead_zone // 2
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            x_start = 0
            y_start = 0
            x_end = x * res_w / 2
            y_end = y * res_h / 2
            segment = [((res_w / 2) + x_start, (res_h // 2) + y_start), ((res_w // 2) + x_end, (res_h // 2) + y_end)]
            img1.line(segment, width = 10)

            # add labels to those divisions
            img_text = Image.new(mode = "RGBA", size = (200, 200), color = (0, 255, 0, 0))
            imgt = ImageDraw.Draw(img_text)
            imgt.text((50, 50), text = str(i), font = font, align = 'center')
            tr = img_text.size
            angle = angle + 2
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            position = (
                int(((res_w // 2) + (x * (res_w // 2.4))) - (tr[0] / 2)),
                int(((res_h // 2) + (y * (res_h // 2.4))) - (tr[1] / 2))
            )
            img.paste(img_text, position, img_text)


        # render and display image
        img = img.resize((res_w // 4, res_h // 4), resample = Image.LANCZOS)
        if(not self.checkbox_invert.isChecked()):
            img = ImageOps.invert(img)
        img.show()

    
    # calculate the expected resistance value for a given temperature value
    # then convert that into the approximate mechancial angle of the potentiometer that will give that resistance value
    # this calculation is done on the deadzone-corrected angular range (self.usable_degrees).
    def get_angle_from_celsius(self, temp: int, resist_ratio: float, dead_zone: int) -> int:
        if self.ysi_400_button.isChecked():
            resistance = (-0.0296102246566647 * (temp ** 3)) + (4.54491006929092 * (temp ** 2)) + (-270.150380192564 * temp) + 6628.80893409997
            resistance = resistance - 1200         # remove minimum resistance expected at lowest setting for calibration
        else:
            resistance = (-0.825010101010102 * (temp ** 3)) + (95.2720346320347 * (temp ** 2)) + (-4461.07128427129 * temp) + 94783.7878787879
            resistance = resistance - 16146         # remove minimum resistance expected at lowest setting for calibration
        
        base_angle = self.usable_degrees - round(resistance / resist_ratio)
        if DEBUG:
            print(f"R: {resistance}, T: {temp}")
            print(f"BA: {base_angle}\n-----\n")
        return(base_angle)
    
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_app = ProtractorGen()
    main_app.show()
    ret = app.exec_()       # main loop call
