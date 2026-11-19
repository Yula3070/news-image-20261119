#!/usr/bin/env python3
"""The Daily Globe, Thursday 19 November 2026 — a one-page front page.

Rendered end to end with PIL into a 1024x1024 PNG. Every picture is a
flat vector shape drawn by the code below: no photographs, no borrowed
artwork, no files fetched from anywhere. The output is deterministic —
running this script twice writes byte-identical PNGs.

Layout from the top of the page down:
  pine masthead with a gold kicker line, then three big illustrated leads,
  then ten illustrated stories in two rows of five, then a BY THE NUMBERS
  strip, then a flat world atlas with numbered pins beside an ALSO list of
  thirty-two short stories, then a sources footer. Forty-five stories in
  all, from six continents.
"""

import hashlib
import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 22
INNER = W - 2 * MARGIN

PAL = {
    "paper": (247, 243, 232),
    "ink": (28, 28, 26),
    "pine": (16, 54, 41),
    "pine_dark": (10, 38, 29),
    "cream": (247, 240, 222),
    "cream_dim": (214, 204, 178),
    "gilt": (208, 170, 64),
    "gilt_soft": (226, 205, 140),
    "ruby": (178, 34, 34),
    "teal": (14, 106, 106),
    "slate": (112, 108, 96),
    "rule": (196, 186, 158),
    "sky": (205, 225, 233),
    "sea": (172, 203, 218),
    "land": (224, 216, 192),
    "land_line": (168, 156, 122),
    "night": (18, 30, 52),
    "deck": (60, 58, 50),
    "white": (255, 255, 255),
}

REGION = {
    "AMERICAS": (34, 120, 60),
    "EUROPE": (36, 84, 160),
    "AFRICA": (176, 110, 32),
    "MIDDLE EAST": (178, 34, 34),
    "ASIA": (176, 132, 20),
    "OCEANIA": (14, 106, 106),
    "GLOBAL": (110, 70, 150),
    "SPACE": (70, 70, 110),
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_FILES = {
    "serif": "DejaVuSerif.ttf",
    "serif-bold": "DejaVuSerif-Bold.ttf",
    "serif-italic": "DejaVuSerif.ttf",  # no serif italic ships here; book face
    "sans": "DejaVuSans.ttf",
    "sans-bold": "DejaVuSans-Bold.ttf",
}
_FACE_CACHE = {}


def face(kind, size):
    """Return a cached DejaVu face; raise loudly when the file is absent."""
    key = (kind, size)
    if key not in _FACE_CACHE:
        path = os.path.join(FONT_DIR, FONT_FILES[kind])
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        _FACE_CACHE[key] = ImageFont.truetype(path, size)
    return _FACE_CACHE[key]


def _box(box, fx0, fy0, fx1, fy1):
    """Absolute box for a fractional sub-box inside (x, y, w, h)."""
    x, y, w, h = box
    return (x + fx0 * w, y + fy0 * h, x + fx1 * w, y + fy1 * h)


def _pt(box, fx, fy):
    """Absolute point for fractional coordinates inside (x, y, w, h)."""
    x, y, w, h = box
    return (x + fx * w, y + fy * h)


class Page:
    """A thin wrapper over ImageDraw with wrap/para/tracked helpers."""

    def __init__(self, w=W, h=H, bg=None):
        self.img = Image.new("RGB", (w, h), bg if bg is not None else PAL["paper"])
        self.d = ImageDraw.Draw(self.img)
        self.w, self.h = w, h

    def rect(self, box, fill=None, outline=None, width=1):
        """Absolute box (x0, y0, x1, y1), PIL-native."""
        self.d.rectangle(box, fill=fill, outline=outline, width=width)

    def fillbox(self, box, fill):
        """Size box (x, y, w, h): fill the rectangle it spans."""
        x, y, w, h = box
        self.d.rectangle([x, y, x + w, y + h], fill=fill)

    def frame(self, box, outline, width=1):
        """Size box (x, y, w, h): draw only its outline."""
        x, y, w, h = box
        self.d.rectangle([x, y, x + w, y + h], outline=outline, width=width)

    def line(self, pts, fill, width=1):
        self.d.line(pts, fill=fill, width=width)

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon(pts, fill=fill, outline=outline)

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.d.ellipse(box, fill=fill, outline=outline, width=width)

    def disc(self, cx, cy, r, fill, outline=None, width=1):
        self.d.ellipse([cx - r, cy - r, cx + r, cy + r],
                       fill=fill, outline=outline, width=width)

    def arc(self, box, start, end, fill, width=1):
        self.d.arc(box, start, end, fill=fill, width=width)

    def text(self, xy, s, font, fill):
        self.d.text(xy, s, font=font, fill=fill)

    def width(self, s, font):
        return self.d.textlength(s, font=font)

    def wrap(self, s, font, width, limit=None):
        """Greedy wrap by pixel width; overlong words are chopped by chars."""
        lines = []
        for word in s.split():
            if lines and self.width(lines[-1] + " " + word, font) <= width:
                lines[-1] += " " + word
                continue
            rest = word
            while self.width(rest, font) > width and len(rest) > 1:
                cut = len(rest)
                while cut > 1 and self.width(rest[:cut], font) > width:
                    cut -= 1
                lines.append(rest[:cut])
                rest = rest[cut:]
            lines.append(rest)
        if limit is not None and len(lines) > limit:
            lines = lines[:limit]
            last = lines[-1]
            while lines and self.width(last + " …", font) > width and last:
                last = last[:-1]
            lines[-1] = (last + " …") if last else "…"
        return lines

    def para(self, x, y, lines, font, fill, leading):
        """Draw wrapped lines top to bottom; return the y below the last."""
        for ln in lines:
            self.text((x, y), ln, font, fill)
            y += leading
        return y

    def caps(self, x, y, s, font, fill, track=2):
        """Uppercase text with manual letter spacing; return the end x."""
        cx = x
        for ch in s:
            self.text((cx, y), ch, font, fill)
            cx += self.width(ch, font) + (track if ch != " " else 4)
        return cx

    def caps_width(self, s, font, track=2):
        total = 0.0
        for ch in s:
            total += self.width(ch, font) + (track if ch != " " else 4)
        return total

    def num_disc(self, cx, cy, n, r=10, fill=None):
        """Filled disc with a white number, for story numbering."""
        self.disc(cx, cy, r, fill or PAL["ruby"])
        f = face("sans-bold", 11 if r <= 10 else 13)
        label = str(n)
        tw = self.width(label, f)
        top = f.getbbox(label)[1]
        bottom = f.getbbox(label)[3]
        self.text((cx - tw / 2, cy - (bottom - top) / 2 - 1), label, f,
                  PAL["white"])

# ---- flat world atlas -----------------------------------------------------
# Hand-authored continent outlines as (lon, lat) pairs. They only have to
# read as a world map at roughly 330 px wide; no coastline is traced.

CONTINENTS = {
    "north_america": [(-168, 66), (-150, 70), (-140, 70), (-128, 71), (-115, 73),
        (-100, 73), (-95, 80), (-85, 76), (-80, 73), (-75, 72), (-68, 62),
        (-60, 55), (-55, 52), (-60, 47), (-66, 45), (-70, 43), (-75, 36),
        (-80, 26), (-84, 30), (-90, 21), (-95, 17), (-100, 16), (-105, 20),
        (-110, 24), (-117, 33), (-124, 40), (-124, 49), (-132, 57),
        (-145, 60), (-158, 58), (-165, 60)],
    "greenland": [(-55, 60), (-45, 60), (-40, 64), (-32, 68), (-22, 70),
        (-20, 74), (-25, 77), (-35, 77), (-45, 76), (-55, 74), (-58, 70),
        (-55, 64)],
    "south_america": [(-80, 9), (-72, 11), (-62, 10), (-52, 5), (-50, 0),
        (-44, -3), (-35, -8), (-38, -15), (-48, -25), (-57, -38), (-65, -41),
        (-70, -52), (-73, -50), (-73, -37), (-70, -20), (-77, -12), (-80, -4)],
    "europe": [(-10, 36), (-9, 43), (-2, 48), (-4, 50), (0, 51), (3, 53),
        (8, 57), (10, 59), (5, 60), (10, 62), (18, 69), (25, 71), (30, 70),
        (40, 68), (45, 66), (40, 60), (35, 55), (30, 50), (28, 45), (23, 40),
        (19, 42), (12, 44), (8, 44), (3, 43), (-2, 37), (-9, 37)],
    "africa": [(-6, 35), (0, 36), (10, 37), (11, 34), (20, 32), (30, 31),
        (35, 28), (37, 22), (40, 15), (43, 11), (48, 11), (51, 10), (41, 0),
        (40, -10), (36, -18), (32, -26), (26, -34), (20, -35), (16, -28),
        (12, -18), (9, -1), (9, 4), (-8, 4), (-13, 8), (-16, 12), (-17, 15),
        (-16, 20), (-15, 27), (-10, 31)],
    "asia": [(40, 68), (45, 66), (50, 69), (60, 69), (70, 72), (80, 73),
        (90, 75), (100, 77), (110, 74), (120, 73), (130, 72), (140, 72),
        (150, 70), (160, 69), (170, 66), (178, 65), (170, 60), (162, 56),
        (158, 52), (150, 59), (142, 54), (140, 46), (135, 43), (130, 42),
        (127, 40), (122, 38), (120, 32), (122, 28), (118, 25), (110, 21),
        (108, 18), (105, 10), (100, 8), (97, 15), (94, 17), (91, 22),
        (88, 22), (86, 20), (80, 15), (77, 8), (74, 20), (70, 23), (66, 25),
        (62, 25), (58, 26), (56, 27), (52, 28), (50, 29), (48, 30), (44, 29),
        (40, 31), (38, 35), (36, 36), (33, 36), (30, 36), (27, 37),
        (26, 40), (30, 44), (35, 50), (40, 55)],
    "oceania": [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33),
        (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
        (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
        (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
        (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
}

MAP_TOP, MAP_BOTTOM = 78.0, -58.0


def project(lon, lat, box):
    """Equirectangular projection of lon/lat into map box (x, y, w, h)."""
    x0, y0, w, h = box
    px = x0 + (lon + 180.0) / 360.0 * w
    py = y0 + (MAP_TOP - lat) / (MAP_TOP - MAP_BOTTOM) * h
    return px, py


def draw_atlas(pg, box, featured, briefs):
    """Flat world map: sea, land polygons, brief dots, numbered pins."""
    x0, y0, w, h = box
    pg.rect((x0, y0, x0 + w, y0 + h), fill=PAL["sea"])
    for outline in CONTINENTS.values():
        pg.poly([project(lon, lat, box) for lon, lat in outline],
                fill=PAL["land"], outline=PAL["land_line"])
    for lon in (-120, -60, 0, 60, 120):
        gx, _ = project(lon, 0, box)
        pg.line([(gx, y0), (gx, y0 + h)], fill=(190, 212, 222))
    for _place, _text, lon, lat, region in briefs:
        px, py = project(lon, lat, box)
        pg.disc(px, py, 2.5, REGION.get(region, PAL["slate"]))
    for story in featured:
        if story.get("lon") is None:
            continue
        px, py = project(story["lon"], story["lat"], box)
        tint = REGION.get(story["region"], PAL["slate"])
        pg.disc(px, py, 9, tint, outline=PAL["white"], width=2)
        f = face("sans-bold", 10)
        label = str(story["num"])
        pg.text((px - pg.width(label, f) / 2, py - 7), label, f, PAL["white"])
    # Voyager 1 is off the map: a corner pin with an arrow pointing out.
    vx, vy = x0 + w - 16, y0 + 14
    pg.disc(vx, vy, 9, REGION["SPACE"], outline=PAL["white"], width=2)
    f = face("sans-bold", 10)
    pg.text((vx - 3, vy - 7), "4", f, PAL["white"])
    pg.line([(vx + 10, vy), (x0 + w + 2, vy)], fill=PAL["ink"])
    pg.text((vx - 64, vy + 11), "to Voyager 1 →", face("sans", 8), PAL["ink"])

# ---- flat illustrations (one per featured story) ---------------------------
# Each sketch paints inside its own box (x, y, w, h). All shapes are
# original PIL primitives; nothing is traced or copied. The subjects are
# new for Thursday 19 November 2026.


def _gta(pg, box):
    pg.fillbox(box, fill=(30, 16, 52))
    for sx, sy in [(0.10, 0.18), (0.28, 0.10), (0.48, 0.16), (0.66, 0.10),
                   (0.84, 0.18), (0.20, 0.30), (0.58, 0.28), (0.76, 0.30)]:
        cx, cy = _pt(box, sx, sy)
        pg.disc(cx, cy, 1, (255, 220, 120))
    pg.ellipse(_box(box, 0.66, 0.06, 0.98, 0.42), fill=(255, 170, 80))
    pg.ellipse(_box(box, 0.70, 0.10, 0.94, 0.38), fill=(255, 200, 120))
    for bx, bw, bh in [(0.04, 0.10, 0.34), (0.16, 0.08, 0.46), (0.26, 0.12, 0.30),
                       (0.40, 0.08, 0.40), (0.50, 0.10, 0.28)]:
        pg.rect(_box(box, bx, 0.66 - bh, bx + bw, 0.66), fill=(16, 10, 34))
    pg.rect(_box(box, 0, 0.66, 1, 1), fill=(14, 60, 90))
    for px in (0.60, 0.88):
        top = _pt(box, px, 0.52)
        pg.line([top, _pt(box, px, 0.72)], fill=(10, 40, 30), width=3)
        for dx, dy in [(-0.06, -0.06), (-0.02, -0.08), (0.03, -0.07), (0.07, -0.05)]:
            pg.line([top, _pt(box, px + dx, 0.52 + dy)], fill=(10, 40, 30), width=2)
    tx, ty = _pt(box, 0.06, 0.44)
    pg.text((tx, ty), "VI", face("serif-bold", 40), (255, 220, 120))
    pg.text((box[0] + 6, box[1] + box[3] - 15), "VICE CITY · GLOBAL LAUNCH",
            face("sans-bold", 9), (230, 210, 250))


def _summit(pg, box):
    pg.fillbox(box, fill=(232, 222, 196))
    heights = [0.30, 0.42, 0.26, 0.50, 0.34, 0.46, 0.30, 0.40, 0.24]
    for i, bx in enumerate([0.06, 0.16, 0.26, 0.36, 0.46, 0.56, 0.66, 0.76, 0.86]):
        pg.rect(_box(box, bx, 0.58 - heights[i], bx + 0.07, 0.58),
                fill=(120, 118, 110))
    pg.rect(_box(box, 0, 0.58, 1, 1), fill=(210, 198, 168))
    pg.ellipse(_box(box, 0.40, 0.52, 0.60, 0.82), fill=(176, 132, 20))
    pg.ellipse(_box(box, 0.44, 0.58, 0.56, 0.76), fill=(232, 222, 196))
    flag_sets = [(0.30, [(200, 40, 40), (255, 255, 255), (40, 60, 160)]),
                 (0.58, [(255, 255, 255), (40, 60, 160), (200, 40, 40)])]
    for fx, cols in flag_sets:
        px, _ = _pt(box, fx, 0)
        pg.line([_pt(box, fx, 0.18), _pt(box, fx, 0.44)], fill=PAL["ink"], width=2)
        for j, col in enumerate(cols):
            pg.rect(_box(box, fx, 0.18 + j * 0.07, fx + 0.10, 0.25 + j * 0.07),
                    fill=col)
    pg.text((box[0] + 6, box[1] + box[3] - 15), "BEIJING · ONE-ON-ONE THU",
            face("sans-bold", 9), (60, 50, 30))


def _court(pg, box):
    pg.fillbox(box, fill=(24, 44, 84))
    pg.poly([_pt(box, 0.10, 0.34), _pt(box, 0.50, 0.10), _pt(box, 0.90, 0.34)],
            fill=(232, 226, 208))
    pg.rect(_box(box, 0.10, 0.34, 0.90, 0.40), fill=(232, 226, 208))
    for cx in (0.16, 0.36, 0.56, 0.76):
        pg.rect(_box(box, cx, 0.40, cx + 0.05, 0.78), fill=(232, 226, 208))
    pg.rect(_box(box, 0.08, 0.78, 0.92, 0.84), fill=(200, 192, 170))
    pg.rect(_box(box, 0.06, 0.84, 0.94, 0.90), fill=(180, 172, 150))
    sx, sy = _pt(box, 0.50, 0.24)
    pg.line([(sx, sy - 8), (sx, sy + 8)], fill=(24, 44, 84), width=2)
    pg.line([(sx - 12, sy - 8), (sx + 12, sy - 8)], fill=(24, 44, 84), width=2)
    pg.poly([(sx - 12, sy - 8), (sx - 18, sy + 2), (sx - 6, sy + 2)],
            fill=(24, 44, 84))
    pg.poly([(sx + 12, sy - 8), (sx + 6, sy + 2), (sx + 18, sy + 2)],
            fill=(24, 44, 84))
    pg.text((box[0] + 6, box[1] + box[3] - 15), "THE HAGUE · WORLD COURT",
            face("sans-bold", 9), (200, 210, 230))


def _voyager(pg, box):
    pg.fillbox(box, fill=(10, 12, 26))
    for sx, sy in [(0.55, 0.12), (0.70, 0.08), (0.94, 0.45), (0.95, 0.62),
                   (0.30, 0.85), (0.55, 0.88), (0.08, 0.55)]:
        cx, cy = _pt(box, sx, sy)
        pg.disc(cx, cy, 1, PAL["white"])
    pg.ellipse(_box(box, -0.05, 0.55, 0.25, 1.05), fill=(50, 110, 180))
    pg.ellipse(_box(box, 0.0, 0.65, 0.16, 0.95), fill=(90, 160, 90))
    for i in range(7):
        cx, cy = _pt(box, 0.40 + i * 0.055, 0.58 - i * 0.045)
        pg.disc(cx, cy, 2, PAL["gilt"])
    px, py = _pt(box, 0.86, 0.18)
    pg.poly([(px - 10, py - 3), (px + 10, py - 3), (px + 3, py + 6),
             (px - 3, py + 6)], fill=(200, 200, 210))
    pg.rect((px - 2, py + 6, px + 2, py + 15), fill=(150, 150, 160))
    pg.text((box[0] + 6, box[1] + 6), "1 LIGHT-DAY",
            face("sans-bold", 10), PAL["gilt"])


def _ipo(pg, box):
    pg.fillbox(box, fill=(16, 40, 32))
    pg.line([_pt(box, 0.06, 0.72), _pt(box, 0.22, 0.58), _pt(box, 0.36, 0.64),
             _pt(box, 0.52, 0.40), _pt(box, 0.68, 0.30)],
            fill=(90, 220, 120), width=3)
    pg.poly([_pt(box, 0.68, 0.30), _pt(box, 0.62, 0.30), _pt(box, 0.68, 0.40)],
            fill=(90, 220, 120))
    bx, by = _pt(box, 0.80, 0.34)
    pg.d.pieslice([bx - 16, by - 14, bx + 16, by + 16], 180, 360, fill=PAL["gilt"])
    pg.rect((bx - 18, by + 12, bx + 18, by + 18), fill=PAL["gilt"])
    pg.ellipse((bx - 3, by + 18, bx + 3, by + 24), fill=PAL["gilt"])
    pg.text(_pt(box, 0.06, 0.10), "$83", face("serif-bold", 18), PAL["white"])
    pg.text(_pt(box, 0.06, 0.42), "A SHARE", face("sans-bold", 9),
            (180, 220, 190))
    pg.text((box[0] + 0.58 * box[2], box[1] + box[3] - 15), "NASDAQ · ANT",
            face("sans-bold", 9), (180, 220, 190))


def _nvidia(pg, box):
    pg.fillbox(box, fill=(18, 26, 18))
    cx, cy = _pt(box, 0.30, 0.50)
    pin = (120, 200, 90)
    for dx in (-26, -14, 0, 14, 26):
        pg.line([(cx + dx, cy - 26), (cx + dx, cy - 34)], fill=pin, width=2)
        pg.line([(cx + dx, cy + 26), (cx + dx, cy + 34)], fill=pin, width=2)
    for dy in (-20, 0, 20):
        pg.line([(cx - 26, cy + dy), (cx - 34, cy + dy)], fill=pin, width=2)
        pg.line([(cx + 26, cy + dy), (cx + 34, cy + dy)], fill=pin, width=2)
    pg.rect((cx - 26, cy - 26, cx + 26, cy + 26), fill=(30, 60, 30),
            outline=pin, width=2)
    pg.rect((cx - 14, cy - 14, cx + 14, cy + 14), fill=pin)
    pg.line([_pt(box, 0.58, 0.78), _pt(box, 0.68, 0.60), _pt(box, 0.76, 0.66),
             _pt(box, 0.92, 0.34)], fill=(90, 220, 120), width=3)
    pg.poly([_pt(box, 0.92, 0.34), _pt(box, 0.86, 0.34), _pt(box, 0.92, 0.44)],
            fill=(90, 220, 120))
    pg.text(_pt(box, 0.52, 0.10), "$115.8bn", face("serif-bold", 16),
            (140, 230, 140))
    pg.text(_pt(box, 0.60, 0.82), "+103% YoY", face("sans-bold", 11),
            (200, 220, 200))

def _gemini(pg, box):
    pg.fillbox(box, fill=(238, 240, 250))
    cx, cy = _pt(box, 0.28, 0.50)
    pg.poly([(cx, cy - 26), (cx + 7, cy - 7), (cx + 26, cy), (cx + 7, cy + 7),
             (cx, cy + 26), (cx - 7, cy + 7), (cx - 26, cy), (cx - 7, cy - 7)],
            fill=(90, 110, 230))
    pg.poly([(cx, cy - 26), (cx + 4, cy - 4), (cx + 26, cy), (cx + 4, cy + 4),
             (cx, cy + 26), (cx - 4, cy + 4), (cx - 26, cy), (cx - 4, cy - 4)],
            fill=(140, 160, 250))
    for sx, sy, r in [(0.05, 0.15, 4), (0.08, 0.72, 3), (0.48, 0.10, 5)]:
        px, py = _pt(box, sx, sy)
        pg.poly([(px, py - r * 2), (px + 1, py - 1), (px + r * 2, py),
                 (px + 1, py + 1), (px, py + r * 2), (px - 1, py + 1),
                 (px - r * 2, py), (px - 1, py - 1)], fill=(176, 132, 220))
    pg.text(_pt(box, 0.56, 0.12), "GEMINI 4", face("serif-bold", 15),
            (40, 50, 120))
    pg.text(_pt(box, 0.56, 0.42), "NEON", face("sans-bold", 11), (90, 110, 230))
    pg.text(_pt(box, 0.56, 0.62), "1M TOKENS", face("sans-bold", 9), PAL["slate"])


def _eu(pg, box):
    pg.fillbox(box, fill=(226, 232, 240))
    pg.rect(_box(box, 0, 0, 1, 0.52), fill=(30, 60, 130))
    cx, cy = _pt(box, 0.26, 0.26)
    r = 0.17 * box[3]
    for i in range(12):
        a = math.pi * 2 * i / 12 - math.pi / 2
        sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        pg.disc(sx, sy, 2, (255, 220, 80))
    pg.rect(_box(box, 0.58, 0.08, 0.92, 0.24), fill=(40, 90, 170))
    pg.rect(_box(box, 0.58, 0.24, 0.92, 0.40), fill=(240, 200, 60))
    pg.text(_pt(box, 0.60, 0.42), "€45bn", face("serif-bold", 20), PAL["ink"])
    pg.text(_pt(box, 0.06, 0.60), "FOR 2027", face("sans-bold", 11), PAL["slate"])
    for bx in [0.08, 0.30, 0.52, 0.74]:
        pg.ellipse(_box(box, bx, 0.76, bx + 0.14, 0.94), fill=PAL["gilt"],
                   outline=(150, 110, 20))
        pg.text(_pt(box, bx + 0.045, 0.78), "€", face("sans-bold", 12),
                (120, 85, 10))


def _australia(pg, box):
    pg.fillbox(box, fill=(206, 226, 232))
    outline_pts = [(0.10, 0.30), (0.22, 0.18), (0.40, 0.14), (0.60, 0.16),
                   (0.78, 0.22), (0.88, 0.34), (0.84, 0.52), (0.70, 0.62),
                   (0.52, 0.70), (0.34, 0.66), (0.18, 0.52), (0.08, 0.40)]
    pg.poly([_pt(box, fx, fy) for fx, fy in outline_pts],
            fill=(224, 200, 140), outline=(150, 120, 60))
    sx, sy = _pt(box, 0.72, 0.48)
    pg.disc(sx, sy, 6, PAL["ruby"])
    pg.text((sx - 3, sy - 5), "*", face("sans-bold", 9), PAL["white"])
    pg.text(_pt(box, 0.06, 0.08), "SANCTIONS", face("sans-bold", 10),
            (20, 60, 90))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "CANBERRA · WEST BANK",
            face("sans-bold", 8), (20, 60, 90))


def _lakers(pg, box):
    pg.fillbox(box, fill=(60, 30, 110))
    cx, cy = _pt(box, 0.26, 0.52)
    pg.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=(240, 130, 40),
               outline=(180, 90, 20), width=2)
    pg.line([(cx - 24, cy), (cx + 24, cy)], fill=(180, 90, 20), width=2)
    pg.line([(cx, cy - 24), (cx, cy + 24)], fill=(180, 90, 20), width=2)
    hx, hy = _pt(box, 0.78, 0.26)
    pg.line([(hx - 16, hy), (hx + 16, hy)], fill=(255, 220, 120), width=3)
    pg.line([(hx - 12, hy), (hx - 8, hy + 18)], fill=PAL["white"], width=1)
    pg.line([(hx + 12, hy), (hx + 8, hy + 18)], fill=PAL["white"], width=1)
    pg.line([(hx - 12, hy + 18), (hx + 12, hy + 18)], fill=PAL["white"], width=1)
    pg.text(_pt(box, 0.52, 0.44), "47", face("serif-bold", 22), (255, 220, 120))
    pg.text(_pt(box, 0.52, 0.72), "OT 118-114", face("sans-bold", 9),
            (220, 200, 250))


def _jakarta(pg, box):
    pg.fillbox(box, fill=(214, 228, 236))
    for bx, bw, bh in [(0.56, 0.10, 0.30), (0.68, 0.08, 0.44), (0.78, 0.12, 0.34)]:
        pg.rect(_box(box, bx, 0.86 - bh, bx + bw, 0.86), fill=(120, 130, 140))
    pg.rect(_box(box, 0, 0.86, 1, 1), fill=(90, 110, 90))
    mx, _ = _pt(box, 0.30, 0)
    top = box[1]
    h = box[3]
    pg.poly([(mx - 10, top + 0.82 * h), (mx - 6, top + 0.18 * h),
             (mx + 6, top + 0.18 * h), (mx + 10, top + 0.82 * h)],
            fill=(240, 238, 230), outline=(150, 145, 130))
    pg.poly([(mx - 7, top + 0.18 * h), (mx, top + 0.06 * h),
             (mx + 7, top + 0.18 * h)], fill=PAL["gilt"])
    pg.ellipse((mx - 3, top + 0.02 * h, mx + 3, top + 0.10 * h),
               fill=(255, 220, 80))
    pg.rect(_box(box, 0.14, 0.82, 0.46, 0.90), fill=(200, 192, 170))
    pg.text(_pt(box, 0.56, 0.10), "JAKARTA", face("sans-bold", 11), (30, 60, 90))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "PALACE SWEEP",
            face("sans-bold", 8), (30, 60, 90))


def _cyclone(pg, box):
    pg.fillbox(box, fill=(206, 226, 232))
    pg.poly([_pt(box, 0.55, 0), _pt(box, 1, 0), _pt(box, 1, 1),
             _pt(box, 0.72, 1), _pt(box, 0.62, 0.55), _pt(box, 0.70, 0.30)],
            fill=(222, 214, 190))
    cx, cy = _pt(box, 0.38, 0.52)
    for k in range(5):
        r1 = 12 + k * 7
        pg.arc((cx - r1, cy - r1, cx + r1, cy + r1), 20 + k * 40, 200 + k * 40,
               fill=(20, 60, 110), width=3)
    pg.disc(cx, cy, 5, (20, 60, 110))
    pg.line([_pt(box, 0.60, 0.30), _pt(box, 0.46, 0.44)], fill=PAL["ruby"], width=2)
    pg.poly([_pt(box, 0.46, 0.44), _pt(box, 0.42, 0.40), _pt(box, 0.42, 0.48)],
            fill=PAL["ruby"])
    pg.text(_pt(box, 0.50, 0.08), "BAY OF BENGAL", face("sans-bold", 9),
            (20, 60, 110))
    pg.text(_pt(box, 0.50, 0.20), "LANDFALL 20 NOV", face("sans-bold", 9),
            PAL["ruby"])


def _markets(pg, box):
    pg.fillbox(box, fill=(240, 234, 220))
    pg.line([_pt(box, 0.06, 0.22), _pt(box, 0.24, 0.34), _pt(box, 0.42, 0.30),
             _pt(box, 0.60, 0.52), _pt(box, 0.78, 0.62), _pt(box, 0.92, 0.78)],
            fill=PAL["ruby"], width=3)
    pg.poly([_pt(box, 0.92, 0.78), _pt(box, 0.92, 0.68), _pt(box, 0.82, 0.78)],
            fill=PAL["ruby"])
    cx, cy = _pt(box, 0.80, 0.24)
    pg.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=PAL["gilt"],
               outline=(150, 110, 20), width=2)
    pg.text((cx - 5, cy - 10), "$", face("serif-bold", 16), (120, 85, 10))
    pg.text(_pt(box, 0.06, 0.08), "5TH DAY DOWN", face("sans-bold", 10),
            PAL["ruby"])
    pg.text((box[0] + 0.06 * box[2], box[1] + box[3] - 15), "S&P 500 -0.5%",
            face("sans-bold", 9), PAL["ink"])


SKETCHES = {
    "gta": _gta,
    "summit": _summit,
    "court": _court,
    "voyager": _voyager,
    "ipo": _ipo,
    "nvidia": _nvidia,
    "gemini": _gemini,
    "eu": _eu,
    "australia": _australia,
    "lakers": _lakers,
    "jakarta": _jakarta,
    "cyclone": _cyclone,
    "markets": _markets,
}

# ---- the day's stories --------------------------------------------------
# Headlines and decks are written here, in my own words, from the day's
# reporting (Reuters, AP, AFP, BBC, Al Jazeera, NASA, ONS, IMD, ANTARA,
# BMKG). Verified facts: GTA VI 99 on Metacritic (Guardian); Trump-Putin
# one-on-one in China, first since Alaska Aug 2025 (AP); ICJ judgment in
# The Gambia v. Myanmar on 19 Nov (ICJ); Voyager 1 one light-day,
# 25.9bn km, NASA confirms 19 Nov (NASA); Anthropic IPO $83, above the
# $70-78 range, ~$1.5tn valuation (Reuters); Nvidia $115.8bn +103%
# (company); Gemini 4 Neon 1m-token model card 18 Nov (DeepMind);
# EU E45bn loan, E70bn gap (FT/Commission); Cyclone Akvan landfall
# 20 Nov, 204,070 to evacuate (IMD); Lakers 118-114 OT, Doncic 36,
# Grimes 47 (AP); S&P 500 -0.50% to 7,304, fifth straight fall,
# Dow -1.32%, gold -2.75% to $3,758 (market data).

FEATURED = [
    {
        "num": 1, "region": "GLOBAL", "topic": "GAMES",
        "headline": "Gamers enter Vice City as GTA VI goes on sale",
        "deck": "The global rollout begins at midnight; the game scores 99 on Metacritic.",
        "sketch": "gta", "lon": -80.2, "lat": 25.8,
    },
    {
        "num": 2, "region": "ASIA", "topic": "SUMMIT",
        "headline": "Trump and Putin meet in China",
        "deck": "First face-to-face since Alaska in August 2025, at the APEC summit.",
        "sketch": "summit", "lon": 114.1, "lat": 22.5,
    },
    {
        "num": 3, "region": "EUROPE", "topic": "COURTS",
        "headline": "World court rules on Myanmar case",
        "deck": "Judges deliver their verdict in The Gambia v. Myanmar over the Rohingya.",
        "sketch": "court", "lon": 4.3, "lat": 52.1,
    },
    {
        "num": 4, "region": "SPACE", "topic": "SCIENCE",
        "headline": "Voyager 1 reaches one light-day",
        "deck": "NASA confirms it; a signal sent today arrives tomorrow.",
        "sketch": "voyager", "lon": None, "lat": None,
    },
    {
        "num": 5, "region": "AMERICAS", "topic": "BUSINESS",
        "headline": "Anthropic IPO priced at $83 a share",
        "deck": "Above the $70-78 range; a $1.5 trillion valuation on debut.",
        "sketch": "ipo", "lon": -74.0, "lat": 40.7,
    },
    {
        "num": 6, "region": "AMERICAS", "topic": "BUSINESS",
        "headline": "Nvidia revenue doubles to $115.8bn",
        "deck": "Sales up 103% on AI demand; shares slip 3% after the report.",
        "sketch": "nvidia", "lon": -122.0, "lat": 37.4,
    },
    {
        "num": 7, "region": "EUROPE", "topic": "TECH",
        "headline": "Google unveils Gemini 4 Neon",
        "deck": "A 1m-token model card; Genie 4 opens to Ultra users.",
        "sketch": "gemini", "lon": -0.1, "lat": 51.5,
    },
    {
        "num": 8, "region": "EUROPE", "topic": "UKRAINE AID",
        "headline": "EU proposes €45bn loan for Ukraine",
        "deck": "Capitals asked to back it; Kyiv faces a €70bn gap.",
        "sketch": "eu", "lon": 4.4, "lat": 50.8,
    },
    {
        "num": 9, "region": "OCEANIA", "topic": "DIPLOMACY",
        "headline": "Australia sanctions Israeli settlers",
        "deck": "West Bank settlers sanctioned; Albanese pictured with Putin.",
        "sketch": "australia", "lon": 149.1, "lat": -35.3,
    },
    {
        "num": 10, "region": "AMERICAS", "topic": "SPORT",
        "headline": "Grimes' 47 lifts Lakers in OT",
        "deck": "Doncic adds 36 as LA rallies from 18 down to win 118-114.",
        "sketch": "lakers", "lon": -118.2, "lat": 34.05,
    },
    {
        "num": 11, "region": "ASIA", "topic": "INDONESIA",
        "headline": "Palace sweeps Prabowo's circle",
        "deck": "Security review after an alleged tap; jobs law passes.",
        "sketch": "jakarta", "lon": 106.8, "lat": -6.2,
    },
    {
        "num": 12, "region": "ASIA", "topic": "WEATHER",
        "headline": "Cyclone Akvan nears India's coast",
        "deck": "Landfall due Friday; 204,070 people told to move.",
        "sketch": "cyclone", "lon": 83.0, "lat": 18.0,
    },
    {
        "num": 13, "region": "AMERICAS", "topic": "MARKETS",
        "headline": "S&P 500 falls for a fifth day",
        "deck": "Fed minutes point to more hikes; gold at a 14-month low.",
        "sketch": "markets", "lon": -77.0, "lat": 38.9,
    },
]

# (place, brief, lon, lat, region) — 32 short stories, numbered 14–45.
BRIEFS = [
    ("Gaza City", "Israeli forces move into central Gaza", 34.5, 31.5, "MIDDLE EAST"),
    ("Baghdad", "Iraq jails six French ISIL recruits for life", 44.4, 33.3, "MIDDLE EAST"),
    ("Chisinau", "Moldova summons Russian envoy over drones", 28.8, 47.0, "EUROPE"),
    ("Madrid", "Police clash with strikers in Spain", -3.7, 40.4, "EUROPE"),
    ("Sacramento", "Atmospheric river floods California", -121.5, 38.6, "AMERICAS"),
    ("Caracas", "Hegseth makes first Venezuela visit", -66.9, 10.5, "AMERICAS"),
    ("Fort Meade", "NSA network outage disrupts spies", -76.8, 39.1, "AMERICAS"),
    ("Frankfurt", "Deutsche Bank's $582m Epstein deals", 8.7, 50.1, "EUROPE"),
    ("Mogadishu", "Somalia accuses UAE of secret bases", 45.3, 2.0, "AFRICA"),
    ("Varna", "Sunken tanker 'hit by projectiles'", 27.5, 43.2, "EUROPE"),
    ("Washington", "US proposes tougher green-card rules", -77.0, 38.9, "AMERICAS"),
    ("Ottawa", "Carney adjusts China ties, eyes US deal", -75.7, 45.4, "AMERICAS"),
    ("Paris", "Mélenchon 'could win' French presidency", 2.35, 48.85, "EUROPE"),
    ("Riyadh", "Saudi Arabia: danger passed in south", 46.7, 24.7, "MIDDLE EAST"),
    ("Benghazi", "Cocaine and millions of pills seized", 20.1, 32.1, "AFRICA"),
    ("Rahway", "Merck launches new rabies vaccine for pets", -74.3, 40.6, "AMERICAS"),
    ("San Francisco", "OpenAI models improve AMD chips 14%", -122.4, 37.8, "AMERICAS"),
    ("Sacramento", "California unveils AI safety plan", -121.5, 38.6, "AMERICAS"),
    ("Shenzhen", "Tencent open-sources 224bn-parameter Hy4", 114.1, 22.5, "ASIA"),
    ("Brussels", "ENISA: AI enables mass cyberattacks", 4.4, 50.8, "EUROPE"),
    ("Washington", "AI cyber threats 'outpace defences'", -77.0, 38.9, "AMERICAS"),
    ("Salt Lake City", "Sensabaugh's 40 ends Jazz skid", -111.9, 40.8, "AMERICAS"),
    ("Philadelphia", "Embiid's 37 lifts 76ers past Nets", -75.2, 39.95, "AMERICAS"),
    ("Houston", "NFL Thursday: Colts visit Texans", -95.4, 29.8, "AMERICAS"),
    ("Vandenberg", "SpaceX Falcon 9 lifts USSF-317", -120.6, 34.6, "AMERICAS"),
    ("Kuala Lumpur", "Malaysia's GDP grows 5.5% in Q3", 101.7, 3.1, "ASIA"),
    ("Jakarta", "Bank Indonesia lifts rate to 6%", 106.8, -6.2, "ASIA"),
    ("Tallinn", "Estonia courts Jakarta on digital ties", 24.7, 59.4, "EUROPE"),
    ("New York", "Bristol-Myers lifts 2026 guidance", -74.0, 40.7, "AMERICAS"),
    ("Palo Alto", "Palo Alto Networks in $4.5bn deal", -122.1, 37.4, "AMERICAS"),
    ("Beijing", "China, Russia deepen ties at APEC", 116.4, 39.9, "ASIA"),
    ("Kyiv", "Zelensky: frontline positions are strong", 30.5, 50.45, "EUROPE"),
]

# BY THE NUMBERS strip: (big figure, caption)
FIGURES = [
    ("99", "GTA VI score on Metacritic at launch"),
    ("$115.8bn", "Nvidia revenue in the quarter, up 103%"),
    ("47", "Quentin Grimes' career-high points for the Lakers"),
    ("$83", "Anthropic's IPO price a share, above its range"),
]

# ---- page composition -----------------------------------------------------

LAYOUT = {
    "lead_x": (MARGIN, 353, 684),
    "lead_w": 318,
    "lead_y": 150,
    "lead_ill": 124,
    "mid_x": (MARGIN, 220, 419, 617, 816),
    "mid_w": 186,
    "row1_y": 400,
    "row2_y": 560,
    "mid_ill": 68,
    "stats_y": 720,
    "bottom_y": 778,
    "footer_y": 1002,
    "rule_y": 392,
}


def draw_masthead(pg):
    pg.rect((0, 0, W, 138), fill=PAL["pine"])
    pg.rect((0, 138, W, 141), fill=PAL["gilt"])
    kicker = face("sans-bold", 13)
    pg.caps(MARGIN, 16, "THE DAILY GLOBE", kicker, PAL["gilt"])
    right = "45 STORIES · 6 CONTINENTS · ONE DAY"
    rw = pg.caps_width(right, kicker)
    pg.caps(W - MARGIN - rw, 16, right, kicker, PAL["gilt"])
    pg.text((MARGIN, 42), "Thursday 19 November 2026",
            face("serif-bold", 54), PAL["cream"])
    pg.text((MARGIN, 108),
            "Every story on this page happened, or was first reported, on this day.",
            face("serif-italic", 14), PAL["cream_dim"])


def draw_tag(pg, x, y, story, small=False):
    pg.num_disc(x + 10, y + 10, story["num"], 10 if small else 11)
    tint = REGION.get(story["region"], PAL["slate"])
    label = story["region"] + " · " + story["topic"]
    pg.text((x + 24, y + 1), label, face("sans-bold", 10 if small else 11), tint)


def draw_lead(pg, story, x):
    box = (x, LAYOUT["lead_y"], LAYOUT["lead_w"], LAYOUT["lead_ill"])
    SKETCHES[story["sketch"]](pg, box)
    pg.frame(box, PAL["rule"])
    ty = LAYOUT["lead_y"] + LAYOUT["lead_ill"] + 6
    draw_tag(pg, x, ty, story)
    hy = ty + 24
    head = face("serif-bold", 24)
    lines = pg.wrap(story["headline"], head, LAYOUT["lead_w"], 2)
    pg.para(x, hy, lines, head, PAL["ink"], 28)
    dy = hy + 28 * len(lines) + 4
    deck = face("sans", 12)
    dlines = pg.wrap(story["deck"], deck, LAYOUT["lead_w"], 2)
    pg.para(x, dy, dlines, deck, PAL["deck"], 15)


def draw_card(pg, story, x, y0):
    box = (x, y0, LAYOUT["mid_w"], LAYOUT["mid_ill"])
    SKETCHES[story["sketch"]](pg, box)
    pg.frame(box, PAL["rule"])
    ty = y0 + LAYOUT["mid_ill"] + 4
    draw_tag(pg, x, ty, story, small=True)
    hy = ty + 22
    head = face("serif-bold", 14)
    lines = pg.wrap(story["headline"], head, LAYOUT["mid_w"], 2)
    pg.para(x, hy, lines, head, PAL["ink"], 17)
    dy = hy + 17 * len(lines) + 2
    deck = face("sans", 10.5)
    dlines = pg.wrap(story["deck"], deck, LAYOUT["mid_w"], 2)
    pg.para(x, dy, dlines, deck, PAL["deck"], 12.5)


def draw_figures(pg):
    sy = LAYOUT["stats_y"]
    pg.line([(MARGIN, sy), (W - MARGIN, sy)], fill=PAL["rule"])
    pg.line([(MARGIN, sy + 50), (W - MARGIN, sy + 50)], fill=PAL["rule"])
    pg.text((MARGIN, sy + 6), "BY THE", face("sans-bold", 12), PAL["ruby"])
    pg.text((MARGIN, sy + 22), "NUMBERS", face("sans-bold", 12), PAL["ruby"])
    sx, sw = 150, 205
    for big, cap in FIGURES:
        pg.text((sx, sy + 2), big, face("serif-bold", 19), PAL["ink"])
        cap_font = face("sans", 10)
        clines = pg.wrap(cap, cap_font, sw - 8, 2)
        pg.para(sx, sy + 26, clines, cap_font, PAL["deck"], 11)
        sx += sw
    pg.line([(sx, sy + 4), (sx, sy + 46)], fill=PAL["rule"])


def draw_bottom(pg):
    by = LAYOUT["bottom_y"]
    pg.text((MARGIN, by), "WHERE IT HAPPENED", face("sans-bold", 11), PAL["ink"])
    map_box = (MARGIN, by + 18, 326, 158)
    draw_atlas(pg, map_box, FEATURED, BRIEFS)
    pg.rect((map_box[0], map_box[1], map_box[0] + map_box[2],
             map_box[1] + map_box[3]), outline=PAL["rule"])
    legend = [[("Americas", (34, 120, 60)), ("Europe", (36, 84, 160)),
               ("Africa", (176, 110, 32)), ("Middle East", (178, 34, 34))],
              [("Asia", (176, 132, 20)), ("Oceania", (14, 106, 106)),
               ("Global", (110, 70, 150))]]
    for ri, row in enumerate(legend):
        ly = by + 182 + ri * 12
        lx = MARGIN
        for name, tint in row:
            pg.disc(lx + 3.5, ly + 5.5, 3.5, tint)
            pg.text((lx + 10, ly), name, face("sans", 9), PAL["ink"])
            lx += 10 + pg.width(name, face("sans", 9)) + 8
    pg.text((MARGIN, by + 208),
            "Numbered pins: stories 1–13 · dots: briefs 14–45.",
            face("sans", 9), PAL["slate"])
    ax = 362
    pg.text((ax, by), "ALSO ON THURSDAY 19 NOVEMBER — 32 MORE STORIES",
            face("sans-bold", 11), PAL["ink"])
    col_x = [ax, ax + 328]
    body = face("sans", 10)
    numf = face("sans-bold", 10)
    placef = face("sans-bold", 10)
    for i, item in enumerate(BRIEFS):
        col = 0 if i < 16 else 1
        row = i % 16
        x = col_x[col]
        y = by + 20 + row * 12.5
        place, text = item[0], item[1]
        num = str(14 + i)
        pg.text((x, y), num, numf, PAL["ruby"])
        nx = x + pg.width(num + " ", numf)
        pg.text((nx, y), place + ": ", placef, PAL["ink"])
        tx = nx + pg.width(place + ": ", placef)
        pg.text((tx, y), text, body, PAL["deck"])


def draw_footer(pg):
    fy = LAYOUT["footer_y"]
    pg.text((MARGIN, fy),
            "Every story on this page was reported on Thursday 19 November 2026; "
            "disputed claims are attributed.",
            face("sans", 9.5), PAL["slate"])
    pg.text((MARGIN, fy + 12),
            "Sources: Reuters, AP, AFP, BBC, Al Jazeera, NASA, ONS, IMD, ANTARA, "
            "BMKG. Original drawings.",
            face("sans", 9.5), PAL["slate"])


def build_page():
    pg = Page()
    draw_masthead(pg)
    for story, x in zip(FEATURED[:3], LAYOUT["lead_x"]):
        draw_lead(pg, story, x)
    pg.line([(MARGIN, LAYOUT["rule_y"]), (W - MARGIN, LAYOUT["rule_y"])],
            fill=PAL["rule"])
    for story, x in zip(FEATURED[3:8], LAYOUT["mid_x"]):
        draw_card(pg, story, x, LAYOUT["row1_y"])
    for story, x in zip(FEATURED[8:13], LAYOUT["mid_x"]):
        draw_card(pg, story, x, LAYOUT["row2_y"])
    draw_figures(pg)
    draw_bottom(pg)
    draw_footer(pg)
    return pg.img


def check_fits():
    """Measure every wrapped block; warn about anything that overflows."""
    meter = Page(4, 4)
    bad = False
    for story in FEATURED[:3]:
        n = len(meter.wrap(story["headline"], face("serif-bold", 24),
                           LAYOUT["lead_w"], 99))
        if n > 2:
            print(f"OVERFLOW lead headline #{story['num']}: {n} lines")
            bad = True
        n = len(meter.wrap(story["deck"], face("sans", 12), LAYOUT["lead_w"], 99))
        if n > 2:
            print(f"OVERFLOW lead deck #{story['num']}: {n} lines")
            bad = True
    for story in FEATURED[3:]:
        n = len(meter.wrap(story["headline"], face("serif-bold", 14),
                           LAYOUT["mid_w"], 99))
        if n > 2:
            print(f"OVERFLOW card headline #{story['num']}: {n} lines")
            bad = True
        n = len(meter.wrap(story["deck"], face("sans", 10.5), LAYOUT["mid_w"], 99))
        if n > 2:
            print(f"OVERFLOW card deck #{story['num']}: {n} lines")
            bad = True
    for i, item in enumerate(BRIEFS):
        total = (meter.width(str(14 + i) + " ", face("sans-bold", 10))
                 + meter.width(item[0] + ": ", face("sans-bold", 10))
                 + meter.width(item[1], face("sans", 10)))
        if total > 312:
            print(f"OVERFLOW also #{14 + i}: {total:.0f}px > 312px")
            bad = True
    title_w = meter.width("Thursday 19 November 2026", face("serif-bold", 54))
    if title_w > INNER:
        print(f"OVERFLOW masthead title: {title_w:.0f}px")
        bad = True
    if not bad:
        print("fits: all blocks within their boxes")
    return not bad


if __name__ == "__main__":
    ok = check_fits()
    page = build_page()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    page.save(out)
    digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
    print(f"wrote {out} sha256={digest} fits_ok={ok}")
