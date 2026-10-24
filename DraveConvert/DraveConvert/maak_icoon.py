# -*- coding: utf-8 -*-
"""Maakt app.ico en logo.ico uit logo.png (het Dravenlock-logo).
Zet je een nieuw logo.png neer? Draai dit script om de .ico's bij te werken.
"""
from PIL import Image

SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main():
    im = Image.open("logo.png").convert("RGBA")
    w, h = im.size
    if w != h:  # vierkant maken (center-crop)
        s = min(w, h); l = (w - s) // 2; t = (h - s) // 2
        im = im.crop((l, t, l + s, t + s))
    im.save("app.ico", sizes=SIZES)
    im.save("logo.ico", sizes=SIZES)
    print("app.ico + logo.ico bijgewerkt uit logo.png")


if __name__ == "__main__":
    main()
