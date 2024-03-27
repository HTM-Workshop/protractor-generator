#!/usr/bin/python3

import math
from PIL import Image, ImageDraw


def main():
    res_w, res_h = 5000, 5000

    img = Image.new(mode = "RGB", size = (res_w, res_h))
    img1 = ImageDraw.Draw(img)

    for i in range(270):
        angle = (360 - i) + 180
        x = math.sin(math.radians(angle))
        y = math.cos(math.radians(angle))
        x_end = x * res_w / 2
        y_end = y * res_h / 2
        segment = [(res_w // 2, res_h // 2), ((res_w // 2) + x_end, (res_h // 2) + y_end)]
        img1.line(segment, width = 10)
        img1 = ImageDraw.Draw(img)

    img = img.resize((res_w // 2, res_h // 2), resample=Image.LANCZOS)
    img.show()


if __name__ == '__main__':
    main()