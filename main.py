#!/usr/bin/python3

import math
from PIL import Image, ImageDraw, ImageFont


def main():
    res_w, res_h = 5000, 5000

    img = Image.new(mode = "RGB", size = (res_w, res_h))
    img1 = ImageDraw.Draw(img)

    font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 90)

    for i in range(0, 281):
        angle = (360 - i) + (180 + 140)
        x = math.sin(math.radians(angle))
        y = math.cos(math.radians(angle))
        x_start = x * (res_w // 2.2) * (bool(i % 10))
        y_start = y * (res_h // 2.2) * (bool(i % 10))
        x_end = x * res_w // 2
        y_end = y * res_h // 2
        segment = [((res_w // 2) + x_start, (res_h // 2) + y_start), ((res_w // 2) + x_end, (res_h // 2) + y_end)]
        img1.line(segment, width = 10)

        if(i % 10) == 0:
            img_text = Image.new(mode = "RGBA", size = (200, 200), color = (0, 255, 0, 0))
            imgt = ImageDraw.Draw(img_text)
            imgt.text((0, 0), text = str(i), font = font)
            #img_text = img_text.rotate(90 + (360 - i), expand = 1)
            position = (
                int((res_w // 2) + (x * (res_w // 2.5))),
                int((res_h // 2) + (y * (res_h // 2.5)))
            )
            img.paste(img_text, position, img_text)
    
    img = img.resize((res_w // 4, res_h // 4), resample = Image.LANCZOS)

    img.show()


if __name__ == '__main__':
    main()