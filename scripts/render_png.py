"""Render a captured terminal transcript (demo/*.txt) to a PNG screenshot. Text is not edited."""
import sys, textwrap
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
COLORS = {"STOP": (255, 95, 95), "BE CAREFUL": (255, 200, 80), "LOOKS OK": (110, 220, 120)}

for path in sys.argv[1:]:
    lines = []
    for l in open(path, encoding="utf-8").read().rstrip().splitlines():
        lines += textwrap.wrap(l, 100, subsequent_indent="  ") or [""]
    font = ImageFont.truetype(FONT, 16)
    w, lh = 100 * 10 + 40, 22
    img = Image.new("RGB", (w, len(lines) * lh + 60), (24, 26, 33))
    d = ImageDraw.Draw(img)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((16 + i * 22, 12, 30 + i * 22, 26), fill=c)
    for i, l in enumerate(lines):
        col = (200, 205, 215)
        if l.startswith("$"): col = (130, 180, 255)
        for k, v in COLORS.items():
            if l.startswith("SECOND LOOK: " + k): col = v
        if l.startswith("("): col = (140, 145, 155)
        d.text((20, 40 + i * lh), l, font=font, fill=col)
    img.save(path[:-4] + ".png")
    print(path[:-4] + ".png", img.size)
