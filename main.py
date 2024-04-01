#!/usr/bin/python3

import math
from PIL import Image, ImageDraw, ImageFont

TEMP_RANGE = range(25, 41)


def get_angle_from_celsius(temp: int) -> int:
    resistance = (-0.0296102246566647 * (temp ** 3)) + (4.54491006929092 * (temp ** 2)) + (-270.150380192564 * temp) + 6628.80893409997
    resistance = resistance - 1200         # remove minimum resistance expected at lowest setting for calibration
    return(280 - round(resistance / 3.57))


def main():
    res_w, res_h = 5000, 5000

    img = Image.new(mode = "RGB", size = (res_w, res_h))
    img1 = ImageDraw.Draw(img)

    font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 90)

    for i in range(-15, 281):
        angle = (360 - i) + (180 + 140)
        x = math.sin(math.radians(angle))
        y = math.cos(math.radians(angle))
        x_start = x * (res_w / 2.2)
        y_start = y * (res_h / 2.2)
        x_end = x * res_w / 2
        y_end = y * res_h / 2
        segment = [((res_w / 2) + x_start, (res_h // 2) + y_start), ((res_w // 2) + x_end, (res_h // 2) + y_end)]
        img1.line(segment, width = 10)

    
    for i in TEMP_RANGE:
        ang = get_angle_from_celsius(i)
        #ang = get_rot_degree(temp_curve(i))
        angle = (360 - ang) + (180 + 140)
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
        imgt.text((0, 0), text = str(i), font = font)
        #img_text = img_text.rotate(90 + (360 - i), expand = 1)
        position = (
            int((res_w // 2) + (x * (res_w // 2.4))),
            int((res_h // 2) + (y * (res_h // 2.4)))
        )
        img.paste(img_text, position, img_text)

    img = img.resize((res_w // 4, res_h // 4), resample = Image.LANCZOS)

    img.show()


if __name__ == '__main__':
    main()