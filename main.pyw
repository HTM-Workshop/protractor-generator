#!/usr/bin/python3
#
#   WARNING: This program and the Temp Sim board are NOT FOR MEDICAL USE!
#
#           Protractor Generator
#   Written by Kevin Williams - 2024
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published byp
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

VERSION = "v1.2"
DEBUG = False

import sys
import math
import images_qr
from PIL import Image, ImageDraw, ImageFont, ImageOps

from webbrowser import Error as wb_error
from webbrowser import open as wb_open
from PyQt5 import QtWidgets, QtCore, QtGui
from protractor_ui import Ui_MainWindow
from about_ui import Ui_Dialog
from license import Ui_license_window

class AboutDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.version.setText(f"Version: {VERSION}")


class LicenseDialog(QtWidgets.QDialog, Ui_license_window):
    def __init__(self, *args, **kwargs):
        super(LicenseDialog, self).__init__(*args, **kwargs)
        self.setupUi(self)


class ProtractorGen(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(ProtractorGen, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(':/icon/icon.png'))
        self.about_window = AboutDialog()
        self.license_window = LicenseDialog()
        self.update_instruction_window()
        self.button_generate.clicked.connect(self.generate_protractor)
        self.radio_resist_no.clicked.connect(self.update_controls)
        self.radio_resist_yes.clicked.connect(self.update_controls)
        self.ysi_400_button.clicked.connect(self.update_controls)
        self.ysi_700_button.clicked.connect(self.update_controls)
        self.action_about.triggered.connect(self.show_about)
        self.action_license.triggered.connect(self.show_license)
        self.action_quit.triggered.connect(sys.exit)
        self.setWindowTitle("Temperature Simulator - Label")
        self._usable_degrees = 0

    def show_license(self):
        self.license_window.show()

    def show_about(self):
        self.about_window.show()
    
    def update_controls(self):
        if self.main_control_frame.isEnabled() == False:
            self.main_control_frame.setEnabled(True)
        if self.radio_resist_yes.isChecked():
            self.standard_select_frame.setEnabled(False)
        else:
            self.standard_select_frame.setEnabled(True)
            self.ysi_400_button.setEnabled(True)
            self.ysi_700_button.setEnabled(True)
        self.update_instruction_window()
        if self.ysi_400_button.isChecked():
            self.spinbox_degrees.setValue(280)
        else:
            self.spinbox_degrees.setValue(300)

    def generate_protractor(self):

        # total mechanical degrees as per the datasheet
        pot_degrees = self.spinbox_degrees.value()

        # calculate the deadzone degrees based on the datasheet's deadzone range
        self.dead_zone = pot_degrees * (self.spinbox_deadzone.value() / 100)

        # usable degrees (mechanical degrees minus deadzone)
        #   This is the final range used for the rest of the program.
        self.usable_degrees = pot_degrees - self.dead_zone

        # calculate ohm ranges with dividing resistors
        #range_ysi400 = (1 / ((1 / self.spinbox_resistance.value()) + (1 / 1500)))
        #range_ysi700 = (1 / ((1 / self.spinbox_resistance.value()) + (1 / 10000)))
        range_ysi400 = self.spinbox_resistance.value()
        range_ysi700 = self.spinbox_resistance.value()

        # calculate change in resistance per angular degree (dR/dA)
        self.rd_ysi400 = range_ysi400 / self.usable_degrees
        self.rd_ysi700 = range_ysi700 / self.usable_degrees

         # graph rotation amount
        self.graph_rot_offset = -1 * ((360 - self.spinbox_degrees.value()) / 2)

        # graph resolution
        self.res_w, self.res_h = 5000, 5000


        if DEBUG:
            print(f"Usable degrees: {self.usable_degrees}")
            print(f"range_ysi400: {range_ysi400}")
            print(f"range_ysi700: {range_ysi700}")
            print(f"rd_ysi400: {self.rd_ysi400}")
            print(f"rd_ysi700: {self.rd_ysi700}")


        # open new image and font
        self.img = Image.new(mode = "RGB", size = (self.res_w, self.res_h))
        self.img1 = ImageDraw.Draw(self.img)
        if sys.platform == 'linux':
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 90)
        elif sys.platform == 'darwin':
            self.font = ImageFont.truetype("/System/Library/Fonts/Keyboard.ttf", 90)
        elif sys.platform == 'win32':
            self.font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 90)
        else:
            self.font = ImageFont.load_default()

        # Draw the outer degree ring.
        for i in range(0, self.spinbox_degrees.value()):
            angle = ((360 - i) + self.graph_rot_offset)
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            x_start = x * (self.res_w / 2.2)
            y_start = y * (self.res_h / 2.2)
            x_end = x * self.res_w / 2
            y_end = y * self.res_h / 2
            segment = [((self.res_w / 2) + x_start, (self.res_h // 2) + y_start), ((self.res_w // 2) + x_end, (self.res_h // 2) + y_end)]
            self.img1.line(segment, width = 10)


        # draw temperature divisions
        if self.radio_resist_yes.isChecked():
            self.draw_temp_divisions(self.rd_ysi400, False, False)
            self.draw_temp_divisions(self.rd_ysi700, True, False)
            label_str = f"Inner: YSI-700\nOuter: YSI-400\nR = {self.spinbox_resistance.value()}"
        elif self.ysi_400_button.isChecked():
            self.draw_temp_divisions(self.rd_ysi400, False, True)
            label_str = f"YSI-400\nR = {self.spinbox_resistance.value()}"
        elif self.ysi_700_button.isChecked():
            self.draw_temp_divisions(self.rd_ysi700, True, True)
            label_str = f"YSI-700\nR = {self.spinbox_resistance.value()}"
        label_str = label_str + f"\n{self.line_custom_label.text()}"
        img_text = Image.new(mode = "RGBA", size = (800, 400), color = (0, 255, 0, 0))
        imgt = ImageDraw.Draw(img_text)
        imgt.text(
            (0, 0), 
            text = label_str, 
            font = self.font, 
            align = 'center'
        )
        position = [100, 100]
        self.img.paste(img_text, position, img_text)

        # draw guidelines
        segment = [1500, self.res_h / 2, self.res_w - 1500, self.res_h / 2]
        self.img1.line(segment, width = 15)
        segment = [self.res_w / 2, 1500, self.res_w / 2, self.res_h - 1500]
        self.img1.line(segment, width = 15)

        # render and display image
        self.img = self.img.resize((self.res_w // 4, self.res_h // 4), resample = Image.LANCZOS)
        if(not self.checkbox_invert.isChecked()):
            self.img = ImageOps.invert(self.img)
        self.img.show()


    def draw_temp_divisions(self, rd_ratio: float, ysi_400: bool, full_lines: bool):

        # temp range to plot
        temp_range = range(40, 1, -1)  

        if full_lines:
            level = 1
        else:
            level = (0.4 * ysi_400) + 1

        for i in temp_range:
            ang = self.get_angle_from_celsius(i, rd_ratio, self.dead_zone, not ysi_400)
            if(ang < 0):
                break
            angle = 360 - (((360 - ang) + self.graph_rot_offset) - self.dead_zone // 2)
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            if full_lines:
                x_start = (x * self.res_w / 4)
                y_start = (y * self.res_h / 4)
            else:
                x_start = (x * self.res_w / (2.7 * level))
                y_start = (y * self.res_h / (2.7 * level))
            x_end = x * self.res_w / (2 * level)
            y_end = y * self.res_h / (2 * level)
            segment = [((self.res_w / 2) + x_start, (self.res_h // 2) + y_start), ((self.res_w // 2) + x_end, (self.res_h // 2) + y_end)]
            self.img1.line(segment, width = 10)   

            # add labels to those divisions
            img_text = Image.new(mode = "RGBA", size = (200, 200), color = (0, 255, 0, 0))
            imgt = ImageDraw.Draw(img_text)
            imgt.text((50, 50), text = str(i), font = self.font, align = 'center')
            tr = img_text.size
            angle = angle + (2 * level)
            x = math.sin(math.radians(angle))
            y = math.cos(math.radians(angle))
            position = (
                int(((self.res_w // 2) + (x * (self.res_w // (2.4 * level)))) - (tr[0] / 2)),
                int(((self.res_h // 2) + (y * (self.res_h // (2.4 * level)))) - (tr[1] / 2))
            )
            self.img.paste(img_text, position, img_text)


    # calculate the expected resistance value for a given temperature value
    # then convert that into the approximate mechancial angle of the potentiometer that will give that resistance value
    # this calculation is done on the deadzone-corrected angular range (self.usable_degrees).
    def get_angle_from_celsius(self, temp: int, resist_ratio: float, dead_zone: int, ysi_400: bool) -> int:
        if ysi_400:
            resistance = (-0.0296102246566647 * (temp ** 3)) + (4.54491006929092 * (temp ** 2)) + (-270.150380192564 * temp) + 6628.80893409997
            #resistance = resistance - 1200         # remove minimum resistance expected at lowest setting for calibration
        else:
            resistance = (-0.0758117011986962 * (temp ** 3)) + (11.816010614772 * (temp ** 2)) + (-710.457138320909 * temp) + 17560.6514816452
            #resistance = resistance - 3196         # remove minimum resistance expected at lowest setting for calibration
        

        # resistance now contains the output goal resistance. Now we need to determine what resistance the main poteniometer
        # needs to be at to return that resistance value. p_res is the resistance value that the main pot in isolation
        # needs to be at for the dividing circuit to output the correct value.
        resistance = resistance + 0.01              # to prevent possible division by zero errors
        if self.radio_resist_yes.isChecked():
            if ysi_400:
                p_res = (-1500 * (resistance - 1200)) / (resistance - 2700)
            else:
                p_res = (-10000 * (resistance - 3196)) / (resistance - 13196)
        else:
            if ysi_400:
                p_res = resistance - 1200
            else:
                p_res = resistance - 3196
        base_angle = self.usable_degrees - round(p_res / resist_ratio)
        if DEBUG:
            print(f"RR: {resist_ratio}")
            print(f"R: {resistance}, T: {temp}")
            print(f"P_RES: {p_res}")
            print(f"BA: {base_angle}\n-----\n")
        return(base_angle)

    def update_instruction_window(self):
        if self.radio_resist_yes.isChecked():
            self.textBrowser.setText("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'Ubuntu'; font-size:13pt; font-weight:400; font-style:normal;">
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:12pt; font-weight:600;">Steps to Calibrate:</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">1. </span>Turn center potentiometer fully counter-clockwise</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">2.</span> Measure resistance between TP3 and TP4. This is your Resistance of Potentiometer. Save this reading for later.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">3.</span> Switch mode switch to 400.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">4.</span> Place multimeter probes in the Meter Probes slots and set to measure resistance.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">5.</span> Turn 2K potentiometer (RV3) until meter reads as close as possbile to 1200 ohms.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">6.</span> Switch mode switch to 700.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">7.</span> Turn 5K potentiometer (RV1) until meter reads as close as possible to 3196 ohms.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">8.</span> Remove meter probes. The device is now calibrated.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">9.</span> Follow the steps to the left to generate a protractor unique to your device.</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /><span style=" font-weight:600;">WARNING</span>: This device and program are for educational purposes only. Do not calibrate active medical equipment using this device.</p></body></html>""")
        elif self.radio_resist_no.isChecked():
            self.textBrowser.setText("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">Steps to Calibrate:</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">For YSI 400:</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt; font-weight:600;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">1. </span><span style=" font-family:'Ubuntu'; font-size:12pt;">Turn center potentiometer fully counter-clockwise</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">2.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Measure resistance between TP3 and TP4. Enter this value into the 'Resistance of Potentiometer' field on the left.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">3.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Place multimeter probes in the Meter Probes slots and set to measure resistance.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">4.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Switch mode switch to YSI 400.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">5.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Turn 2K potentiometer (RV3) until meter reads as close as possbile to 1200 ohms.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">6.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Remove meter probes. The device is now calibrated.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">7.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Follow the steps to the left to generate a protractor unique to your device.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-style:italic;">Note: For YSI 400, the default mechanical range is 280 degrees.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">For YSI 700:</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt; font-weight:600;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">1. </span><span style=" font-family:'Ubuntu'; font-size:12pt;">Turn center potentiometer fully counter-clockwise</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">2.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Measure resistance between TP3 and TP4. Enter this value into the 'Resistance of Potentiometer' field on the left.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">3.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Place multimeter probes in the Meter Probes slots and set to measure resistance.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">4.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Switch mode switch to YSI 700.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">5.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Turn 5K potentiometer (RV1) until meter reads as close as possible to 3196 ohms.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">6.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Remove meter probes. The device is now calibrated.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">7.</span><span style=" font-family:'Ubuntu'; font-size:12pt;"> Follow the steps to the left to generate a protractor unique to your device.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt; font-style:italic;">Note: For YSI 700, the default mechanical range is 300 degrees.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Ubuntu'; font-size:12pt;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Ubuntu'; font-size:12pt;"><br /></span><span style=" font-family:'Ubuntu'; font-size:12pt; font-weight:600;">WARNING</span><span style=" font-family:'Ubuntu'; font-size:12pt;">: This device and program are for educational purposes only. Do not calibrate active medical equipment using this device.</span></p></body></html>""")
        else:
            self.textBrowser.setText("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'Ubuntu'; font-size:13pt; font-weight:400; font-style:normal;">
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:12pt; font-weight:600;">Steps to Calibrate:</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">1. </span>First, select an option for the first question on the left.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /><span style=" font-weight:600;">WARNING</span>: This device and program are for educational purposes only. Do not calibrate active medical equipment using this device.</p></body></html>""")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_app = ProtractorGen()
    main_app.show()
    ret = app.exec_()       # main loop call
