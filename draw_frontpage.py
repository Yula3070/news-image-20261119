#!/usr/bin/env python3
"""The Daily Globe, Thursday 19 November 2026 — Round 3 front page.

Rendered end to end with PIL into a 1024x1024 PNG. Every picture is a
flat vector shape drawn by the code below: no photographs, no borrowed
artwork, no files fetched from anywhere. The output is deterministic —
running this script twice writes byte-identical PNGs.

Round 3 rebuilds the page on the structure the day's strongest front
pages share, with our own drawings and our own words throughout:
  cream masthead with the date as the headline, a region strip whose
  counts are computed from the story list, a big-number strip, three
  illustrated leads, ten illustrated stories in two rows of five, a
  larger world atlas with numbered pins beside twenty-nine short
  stories, a DATE CHECK box that keeps Wednesday's news out of
  Thursday's page, then a sources footer. Forty-two stories in all.

Date discipline (the Round 2 lesson): Round 2 counted as Thursday
stories that were first reported on Wednesday 18 November — the
Voyager 1 one-light-day crossing, the EU's proposed 45bn loan, the
Gemini 4 model card. Round 3 moves those into the DATE CHECK box and
leads with the three stories the whole day agrees on: the first
three-way summit in Shenzhen, GTA VI's release day, and Anthropic's
record IPO. The summit is a three-way meeting — Trump, Xi and Putin —
not a two-way one.
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
    "cream": (247, 240, 222),
    "cream_dim": (214, 204, 178),
    "gilt": (208, 170, 64),
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
}

# Region strip order: (label, regions counted under it, tab colour)
STRIP = [
    ("EUROPE", ["EUROPE"], (36, 84, 160)),
    ("THE AMERICAS", ["AMERICAS"], (34, 120, 60)),
    ("ASIA-PACIFIC", ["ASIA"], (176, 132, 20)),
    ("MIDEAST", ["MIDDLE EAST"], (178, 34, 34)),
    ("AFRICA", ["AFRICA"], (176, 110, 32)),
    ("OCEANIA", ["OCEANIA"], (14, 106, 106)),
    ("WORLD", ["GLOBAL"], (110, 70, 150)),
]

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
        pg.disc(px, py, 10, tint, outline=PAL["white"], width=2)
        f = face("sans-bold", 11)
        label = str(story["num"])
        pg.text((px - pg.width(label, f) / 2, py - 8), label, f, PAL["white"])

# ---- flat illustrations (one per featured story) ---------------------------
# Each sketch paints inside its own box (x, y, w, h). All shapes are
# original PIL primitives drawn for this round; nothing is traced or
# copied. The subjects are new for Thursday 19 November 2026.


def _flag_us(pg, x, y, w, h):
    """Stars-and-stripes flag in a small box (x, y, w, h)."""
    for i in range(7):
        pg.rect((x, y + i * h / 7, x + w, y + (i + 1) * h / 7),
                fill=(178, 34, 34) if i % 2 == 0 else PAL["white"])
    pg.rect((x, y, x + w * 0.42, y + h * 4 / 7), fill=(30, 50, 120))
    for r in range(3):
        for c in range(4):
            pg.disc(x + w * 0.06 + c * w * 0.10,
                    y + h * 0.07 + r * h * 0.12, 1.2, PAL["white"])


def _flag_cn(pg, x, y, w, h):
    """China flag in a small box."""
    pg.rect((x, y, x + w, y + h), fill=(200, 30, 30))
    pg.disc(x + w * 0.22, y + h * 0.28, 3.5, (255, 220, 80))
    for dx, dy in [(0.42, 0.14), (0.52, 0.30), (0.50, 0.48), (0.36, 0.52)]:
        pg.disc(x + w * dx, y + h * dy, 1.8, (255, 220, 80))


def _flag_ru(pg, x, y, w, h):
    """Russia tricolour in a small box."""
    pg.rect((x, y, x + w, y + h / 3), fill=PAL["white"])
    pg.rect((x, y + h / 3, x + w, y + 2 * h / 3), fill=(30, 80, 180))
    pg.rect((x, y + 2 * h / 3, x + w, y + h), fill=(200, 30, 30))


def _summit3(pg, box):
    """Three-way summit: three flags over a skyline and a round table."""
    pg.fillbox(box, fill=(232, 222, 196))
    for bx, bw, bh in [(0.04, 0.09, 0.30), (0.15, 0.07, 0.44), (0.24, 0.10, 0.28),
                       (0.66, 0.08, 0.40), (0.76, 0.10, 0.26), (0.88, 0.07, 0.36)]:
        pg.rect(_box(box, bx, 0.58 - bh, bx + bw, 0.58), fill=(120, 118, 110))
    pg.rect(_box(box, 0, 0.58, 1, 1), fill=(210, 198, 168))
    pg.ellipse(_box(box, 0.38, 0.52, 0.62, 0.80), fill=(176, 132, 20))
    pg.ellipse(_box(box, 0.42, 0.58, 0.58, 0.76), fill=(232, 222, 196))
    poles = [(0.12, _flag_us), (0.42, _flag_cn), (0.72, _flag_ru)]
    for fx, draw_flag in poles:
        px, _ = _pt(box, fx, 0)
        pg.line([_pt(box, fx, 0.06), _pt(box, fx, 0.52)], fill=PAL["ink"], width=2)
        fw = 0.20 * box[2]
        fh = 0.20 * box[3]
        draw_flag(pg, px, box[1] + 0.06 * box[3], fw, fh)
    pg.text((box[0] + 6, box[1] + box[3] - 15), "SHENZHEN · APEC",
            face("sans-bold", 9), (60, 50, 30))


def _gta(pg, box):
    """Vice City at dusk: sunset bands, skyline, palms, big VI."""
    pg.fillbox(box, fill=(46, 18, 66))
    pg.rect(_box(box, 0, 0.30, 1, 0.46), fill=(150, 60, 110))
    pg.rect(_box(box, 0, 0.46, 1, 0.62), fill=(230, 120, 80))
    for sx, sy in [(0.08, 0.10), (0.24, 0.06), (0.44, 0.12), (0.62, 0.06),
                   (0.82, 0.10), (0.16, 0.22), (0.56, 0.20), (0.74, 0.24)]:
        cx, cy = _pt(box, sx, sy)
        pg.disc(cx, cy, 1, (255, 220, 120))
    pg.ellipse(_box(box, 0.36, 0.10, 0.64, 0.52), fill=(255, 190, 90))
    pg.ellipse(_box(box, 0.40, 0.16, 0.60, 0.46), fill=(255, 220, 140))
    for bx, bw, bh in [(0.02, 0.10, 0.30), (0.14, 0.08, 0.42), (0.24, 0.12, 0.26),
                       (0.68, 0.09, 0.36), (0.79, 0.11, 0.28), (0.90, 0.07, 0.32)]:
        pg.rect(_box(box, bx, 0.66 - bh, bx + bw, 0.66), fill=(20, 10, 40))
    pg.rect(_box(box, 0, 0.66, 1, 1), fill=(14, 60, 90))
    for px in (0.58, 0.90):
        top = _pt(box, px, 0.50)
        pg.line([top, _pt(box, px, 0.70)], fill=(10, 40, 30), width=3)
        for dx, dy in [(-0.06, -0.06), (-0.02, -0.08), (0.03, -0.07), (0.07, -0.05)]:
            pg.line([top, _pt(box, px + dx, 0.50 + dy)], fill=(10, 40, 30), width=2)
    pg.text(_pt(box, 0.05, 0.40), "VI", face("serif-bold", 40), (255, 220, 120))
    pg.text((box[0] + 6, box[1] + box[3] - 15), "VICE CITY · OUT TODAY",
            face("sans-bold", 9), (230, 210, 250))


def _ipo(pg, box):
    """Anthropic IPO: green candlesticks climbing to $83 on a dark board."""
    pg.fillbox(box, fill=(16, 40, 32))
    candles = [(0.08, 0.62, 0.70, 0.16), (0.20, 0.52, 0.60, 0.16),
               (0.32, 0.56, 0.62, 0.16), (0.44, 0.38, 0.48, 0.16),
               (0.56, 0.42, 0.50, 0.16), (0.68, 0.26, 0.36, 0.16)]
    for fx, fy0, fy1, fw in candles:
        pg.rect(_box(box, fx, fy0, fx + fw, fy1), fill=(90, 220, 120))
        pg.line([_pt(box, fx + fw / 2, fy0 - 0.06),
                 _pt(box, fx + fw / 2, fy1 + 0.06)], fill=(90, 220, 120), width=2)
    pg.line([_pt(box, 0.06, 0.74), _pt(box, 0.22, 0.60), _pt(box, 0.36, 0.64),
             _pt(box, 0.52, 0.44), _pt(box, 0.68, 0.34), _pt(box, 0.84, 0.20)],
            fill=(255, 220, 120), width=3)
    pg.poly([_pt(box, 0.84, 0.20), _pt(box, 0.78, 0.20), _pt(box, 0.84, 0.30)],
            fill=(255, 220, 120))
    pg.text(_pt(box, 0.06, 0.06), "$83", face("serif-bold", 20), PAL["white"])
    pg.text(_pt(box, 0.06, 0.34), "ANT · NASDAQ", face("sans-bold", 9),
            (180, 220, 190))
    pg.text((box[0] + 0.62 * box[2], box[1] + box[3] - 15), "FIRST TRADE TODAY",
            face("sans-bold", 9), (180, 220, 190))


def _court(pg, box):
    """World Court: pediment, columns and scales on deep blue."""
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


def _cop31(pg, box):
    """COP31: sun over hills, a globe, and a long negotiating table."""
    pg.fillbox(box, fill=(222, 232, 226))
    pg.ellipse(_box(box, 0.68, 0.08, 0.94, 0.44), fill=(255, 190, 90))
    pg.ellipse(_box(box, 0.72, 0.14, 0.90, 0.38), fill=(255, 220, 140))
    pg.poly([_pt(box, 0, 0.55), _pt(box, 0.30, 0.30), _pt(box, 0.60, 0.55),
             _pt(box, 1, 0.38), _pt(box, 1, 1), _pt(box, 0, 1)],
            fill=(90, 140, 90))
    pg.poly([_pt(box, 0, 0.70), _pt(box, 0.40, 0.48), _pt(box, 0.75, 0.70),
             _pt(box, 1, 0.58), _pt(box, 1, 1), _pt(box, 0, 1)],
            fill=(60, 110, 70))
    cx, cy = _pt(box, 0.22, 0.62)
    pg.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(60, 120, 180),
               outline=(30, 80, 140), width=2)
    pg.ellipse((cx - 10, cy - 12, cx - 2, cy - 2), fill=(90, 160, 90))
    pg.ellipse((cx + 2, cy + 2, cx + 10, cy + 12), fill=(90, 160, 90))
    pg.rect(_box(box, 0.48, 0.72, 0.96, 0.80), fill=(120, 90, 60))
    for fx in (0.54, 0.66, 0.78, 0.90):
        pg.rect(_box(box, fx - 0.02, 0.64, fx + 0.02, 0.72), fill=(240, 240, 230))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "ANTALYA · FINAL 48 HOURS",
            face("sans-bold", 8), (30, 60, 40))


def _cyclone(pg, box):
    """Cyclone Akvan: spiral over the Bay of Bengal, labels kept clear."""
    pg.fillbox(box, fill=(206, 226, 232))
    pg.poly([_pt(box, 0.58, 0), _pt(box, 1, 0), _pt(box, 1, 1),
             _pt(box, 0.74, 1), _pt(box, 0.64, 0.55), _pt(box, 0.72, 0.30)],
            fill=(222, 214, 190))
    cx, cy = _pt(box, 0.36, 0.50)
    for k in range(5):
        r1 = 11 + k * 6
        pg.arc((cx - r1, cy - r1, cx + r1, cy + r1), 20 + k * 40, 200 + k * 40,
               fill=(20, 60, 110), width=3)
    pg.disc(cx, cy, 5, (20, 60, 110))
    pg.line([_pt(box, 0.58, 0.28), _pt(box, 0.46, 0.42)], fill=PAL["ruby"], width=2)
    pg.poly([_pt(box, 0.46, 0.42), _pt(box, 0.42, 0.38), _pt(box, 0.42, 0.46)],
            fill=PAL["ruby"])
    lx, ly = _pt(box, 0.03, 0.03)
    pg.rect((lx, ly, lx + 112, ly + 30), fill=(206, 226, 232))
    pg.text(_pt(box, 0.06, 0.06), "BAY OF BENGAL", face("sans-bold", 9),
            (20, 60, 110))
    pg.text(_pt(box, 0.06, 0.20), "LANDFALL FRI", face("sans-bold", 9),
            PAL["ruby"])


def _kyiv(pg, box):
    """Kyiv: golden domes under a blue-and-yellow sky."""
    pg.fillbox(box, fill=(120, 170, 220))
    pg.rect(_box(box, 0, 0.52, 1, 1), fill=(240, 220, 130))
    pg.rect(_box(box, 0, 0.52, 1, 0.62), fill=(255, 215, 0))
    pg.rect(_box(box, 0, 0.62, 1, 0.72), fill=(40, 90, 180))
    for cx, cw, ch in [(0.18, 0.10, 0.30), (0.34, 0.08, 0.40), (0.48, 0.12, 0.34),
                       (0.64, 0.08, 0.44), (0.78, 0.10, 0.30)]:
        pg.rect(_box(box, cx, 0.72 - ch, cx + cw, 0.72), fill=(90, 80, 70))
        dx = cx + cw / 2
        pg.ellipse(_box(box, dx - 0.05, 0.72 - ch - 0.12, dx + 0.05, 0.72 - ch),
                   fill=(255, 200, 60))
        pg.line([_pt(box, dx, 0.72 - ch - 0.12), _pt(box, dx, 0.72 - ch - 0.20)],
                fill=(90, 80, 70), width=1)
    pg.text((box[0] + 6, box[1] + box[3] - 13), "KYIV · OFF THE AGENDA",
            face("sans-bold", 8), (30, 50, 90))


def _apec(pg, box):
    """APEC declaration: a signed document, small flags along the top."""
    pg.fillbox(box, fill=(226, 232, 240))
    for i in range(6):
        col = [(178, 34, 34), (34, 120, 60), (36, 84, 160)][i % 3]
        pg.rect(_box(box, 0.05 + i * 0.16, 0.06, 0.17 + i * 0.16, 0.20),
                fill=col)
    pg.rect(_box(box, 0.16, 0.30, 0.84, 0.92), fill=PAL["white"],
            outline=(150, 140, 110))
    pg.rect(_box(box, 0.16, 0.30, 0.84, 0.44), fill=(16, 54, 41))
    pg.text(_pt(box, 0.20, 0.33), "DECLARATION", face("sans-bold", 9),
            PAL["white"])
    for i, wy in enumerate((0.52, 0.64, 0.76)):
        pg.line([_pt(box, 0.22, wy), _pt(box, 0.78, wy)], fill=(180, 172, 150))
    pg.poly([_pt(box, 0.62, 0.82), _pt(box, 0.70, 0.82), _pt(box, 0.66, 0.88)],
            fill=(178, 34, 34))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "21 ECONOMIES SIGN",
            face("sans-bold", 8), (30, 50, 90))


def _florida(pg, box):
    """Flooded Florida: rain over a drowned street and a palm."""
    pg.fillbox(box, fill=(150, 180, 205))
    for sx in (0.10, 0.26, 0.44, 0.62, 0.80, 0.92):
        pg.line([_pt(box, sx, 0.06), _pt(box, sx - 0.02, 0.22)],
                fill=(90, 120, 150), width=2)
    pg.rect(_box(box, 0, 0.62, 1, 1), fill=(70, 110, 150))
    for bx, bw, bh in [(0.04, 0.12, 0.22), (0.20, 0.10, 0.30), (0.66, 0.12, 0.26),
                       (0.82, 0.10, 0.20)]:
        pg.rect(_box(box, bx, 0.62 - bh, bx + bw, 0.62), fill=(90, 85, 80))
    top = _pt(box, 0.48, 0.30)
    pg.line([top, _pt(box, 0.48, 0.62)], fill=(60, 50, 40), width=3)
    for dx, dy in [(-0.08, -0.06), (-0.03, -0.09), (0.04, -0.08), (0.09, -0.05)]:
        pg.line([top, _pt(box, 0.48 + dx, 0.30 + dy)], fill=(60, 50, 40), width=2)
    pg.ellipse(_box(box, 0.30, 0.66, 0.38, 0.72), fill=(220, 225, 230))
    pg.ellipse(_box(box, 0.60, 0.70, 0.72, 0.76), fill=(220, 225, 230))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "HOLLYWOOD · 300 CALLS",
            face("sans-bold", 8), (20, 50, 80))


def _paris(pg, box):
    """Paris: Eiffel Tower silhouette and a ballot box."""
    pg.fillbox(box, fill=(214, 226, 236))
    tx, ty = _pt(box, 0.30, 0.86)
    pg.poly([(tx - 16, ty), (tx - 4, ty - 52), (tx, ty - 66), (tx + 4, ty - 52),
             (tx + 16, ty)], fill=(70, 70, 80))
    pg.line([(tx - 12, ty - 22), (tx + 12, ty - 22)], fill=(70, 70, 80), width=2)
    pg.line([(tx - 7, ty - 40), (tx + 7, ty - 40)], fill=(70, 70, 80), width=2)
    pg.rect(_box(box, 0.56, 0.52, 0.90, 0.86), fill=(200, 60, 60),
            outline=(140, 30, 30), width=2)
    pg.rect(_box(box, 0.66, 0.44, 0.80, 0.52), fill=(240, 240, 230),
            outline=(140, 30, 30), width=2)
    pg.ellipse(_box(box, 0.68, 0.60, 0.78, 0.74), fill=PAL["white"])
    pg.text(_pt(box, 0.70, 0.60), "✓", face("sans-bold", 12), (200, 60, 60))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "PARIS · BALLOT 2027",
            face("sans-bold", 8), (30, 50, 90))


def _saudi(pg, box):
    """Saudi all-clear: desert dunes, a downed missile trail, clear sky."""
    pg.fillbox(box, fill=(240, 220, 180))
    pg.ellipse(_box(box, 0.70, 0.06, 0.94, 0.40), fill=(255, 220, 120))
    pg.poly([_pt(box, 0, 0.62), _pt(box, 0.35, 0.44), _pt(box, 0.70, 0.62),
             _pt(box, 1, 0.50), _pt(box, 1, 1), _pt(box, 0, 1)],
            fill=(220, 190, 130))
    pg.poly([_pt(box, 0, 0.78), _pt(box, 0.45, 0.62), _pt(box, 0.85, 0.78),
             _pt(box, 1, 0.70), _pt(box, 1, 1), _pt(box, 0, 1)],
            fill=(200, 165, 100))
    pg.line([_pt(box, 0.10, 0.30), _pt(box, 0.30, 0.22), _pt(box, 0.48, 0.26)],
            fill=(120, 120, 130), width=2)
    pg.poly([_pt(box, 0.48, 0.26), _pt(box, 0.42, 0.24), _pt(box, 0.44, 0.30)],
            fill=(120, 120, 130))
    pg.ellipse(_box(box, 0.56, 0.14, 0.66, 0.28), fill=(255, 255, 255),
               outline=(34, 120, 60), width=2)
    pg.text(_pt(box, 0.585, 0.15), "✓", face("sans-bold", 10), (34, 120, 60))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "JAZAN · ALL CLEAR",
            face("sans-bold", 8), (90, 60, 20))


def _libya(pg, box):
    """Libya seizure: port crates stamped SEIZED under a crane."""
    pg.fillbox(box, fill=(200, 210, 220))
    pg.line([_pt(box, 0.12, 0.10), _pt(box, 0.12, 0.55)], fill=(60, 60, 70),
            width=4)
    pg.line([_pt(box, 0.12, 0.10), _pt(box, 0.80, 0.10)], fill=(60, 60, 70),
            width=4)
    pg.line([_pt(box, 0.80, 0.10), _pt(box, 0.80, 0.30)], fill=(60, 60, 70),
            width=2)
    pg.rect(_box(box, 0.72, 0.30, 0.88, 0.44), fill=(180, 60, 50))
    pg.rect(_box(box, 0.10, 0.58, 0.34, 0.80), fill=(40, 90, 140))
    pg.rect(_box(box, 0.38, 0.58, 0.62, 0.80), fill=(200, 140, 40))
    pg.rect(_box(box, 0.66, 0.58, 0.90, 0.80), fill=(90, 120, 80))
    pg.rect(_box(box, 0.30, 0.66, 0.70, 0.78), fill=PAL["white"],
            outline=PAL["ruby"], width=2)
    pg.text(_pt(box, 0.34, 0.68), "SEIZED", face("sans-bold", 10), PAL["ruby"])
    pg.rect(_box(box, 0, 0.84, 1, 1), fill=(70, 110, 150))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "BENGHAZI · PORT RAID",
            face("sans-bold", 8), (20, 50, 80))


def _geology(pg, box):
    """Earth's missing billion years: rock strata and a magnifier."""
    pg.fillbox(box, fill=(232, 224, 205))
    bands = [(0.62, (150, 120, 80)), (0.70, (120, 100, 70)),
             (0.78, (90, 80, 60)), (0.86, (170, 140, 100)),
             (0.94, (110, 90, 65))]
    for fy, col in bands:
        pg.rect(_box(box, 0, fy - 0.08, 1, fy), fill=col)
    pg.line([_pt(box, 0.10, 0.62), _pt(box, 0.30, 0.50), _pt(box, 0.55, 0.60),
             _pt(box, 0.80, 0.46), _pt(box, 0.95, 0.54)],
            fill=(60, 50, 40), width=2)
    cx, cy = _pt(box, 0.62, 0.32)
    pg.ellipse((cx - 20, cy - 20, cx + 20, cy + 20), fill=(200, 225, 235),
               outline=(40, 60, 90), width=3)
    pg.line([(cx + 14, cy + 14), (cx + 30, cy + 30)], fill=(40, 60, 90), width=4)
    pg.ellipse((cx - 10, cy - 12, cx - 2, cy + 2), fill=(90, 130, 90))
    pg.ellipse((cx + 2, cy + 4, cx + 10, cy + 12), fill=(120, 100, 70))
    pg.text((box[0] + 6, box[1] + box[3] - 13), "1BN YEARS FOUND",
            face("sans-bold", 8), (60, 50, 30))


SKETCHES = {
    "summit3": _summit3,
    "gta": _gta,
    "ipo": _ipo,
    "court": _court,
    "cop31": _cop31,
    "cyclone": _cyclone,
    "kyiv": _kyiv,
    "apec": _apec,
    "florida": _florida,
    "paris": _paris,
    "saudi": _saudi,
    "libya": _libya,
    "geology": _geology,
}

# ---- the day's stories --------------------------------------------------
# Headlines and decks are written here, in my own words, from the day's
# reporting (Reuters, AP, AFP, BBC, The Hindu, IMD, NASA, ICJ, Pew).
# Thursday 19 November 2026, verified as first reported that day:
# the first three-way summit in Shenzhen (AP); GTA VI unlocks at
# midnight, 15.9m pre-orders (Rockstar/retail); Anthropic IPO priced
# $83, $81.3bn raised, ~$1.5tn valuation (Reuters); ICJ judgment in
# The Gambia v. Myanmar (ICJ); COP31 final 48 hours, $120bn adaptation
# fund open (UNFCCC); Cyclone Akvan, 200,000 to evacuate, landfall
# Friday near Puri (IMD); APEC adopts the Shenzhen Declaration
# (APEC); Florida floods, 300 rescue calls (local reports); Mélenchon
# a plausible president, justice minister concedes (French press);
# Saudi all-clear after a Houthi missile downed (Saudi press);
# Libya's biggest drug seizure in Benghazi (Libyan officials);
# Earth's missing billion years explained, Nature study (Nature).

FEATURED = [
    {
        "num": 1, "region": "ASIA", "topic": "SUMMIT",
        "headline": "Three leaders hold first three-way summit",
        "deck": "The three nuclear powers meet at APEC; arms control and Iran top the agenda.",
        "sketch": "summit3", "lon": 114.1, "lat": 22.5,
    },
    {
        "num": 2, "region": "GLOBAL", "topic": "GAMES",
        "headline": "GTA VI arrives after a 13-year wait",
        "deck": "Unlocks at midnight worldwide, New Zealand first; 15.9m pre-orders banked.",
        "sketch": "gta", "lon": -80.2, "lat": 25.8,
    },
    {
        "num": 3, "region": "AMERICAS", "topic": "MARKETS",
        "headline": "Anthropic in the biggest IPO on record",
        "deck": "Priced at $83, the Claude maker raised $81.3bn and is valued near $1.5tn.",
        "sketch": "ipo", "lon": -74.0, "lat": 40.7,
    },
    {
        "num": 4, "region": "EUROPE", "topic": "LAW",
        "headline": "World Court rules on Rohingya case",
        "deck": "The ICJ reads its judgment in The Gambia's case.",
        "sketch": "court", "lon": 4.3, "lat": 52.1,
    },
    {
        "num": 5, "region": "EUROPE", "topic": "CLIMATE",
        "headline": "COP31 enters its final 48 hours",
        "deck": "Ministers take over; the $120bn fund stays open.",
        "sketch": "cop31", "lon": 30.7, "lat": 36.9,
    },
    {
        "num": 6, "region": "ASIA", "topic": "STORM",
        "headline": "Akvan bears down as 200,000 flee the coast",
        "deck": "Red alerts in 11 districts; landfall near Puri Friday.",
        "sketch": "cyclone", "lon": 83.0, "lat": 18.0,
    },
    {
        "num": 7, "region": "EUROPE", "topic": "WAR",
        "headline": "Ukraine left off the Shenzhen agenda",
        "deck": "The war will not be raised, the White House says.",
        "sketch": "kyiv", "lon": 30.5, "lat": 50.45,
    },
    {
        "num": 8, "region": "ASIA", "topic": "TRADE",
        "headline": "APEC leaders adopt the Shenzhen Declaration",
        "deck": "Twenty-one economies back digital trade and a joint roadmap.",
        "sketch": "apec", "lon": 114.1, "lat": 22.5,
    },
    {
        "num": 9, "region": "AMERICAS", "topic": "WEATHER",
        "headline": "Flooded Florida braces for still more rain",
        "deck": "A foot of rain in Hollywood; 300 rescue calls in a night.",
        "sketch": "florida", "lon": -80.2, "lat": 26.0,
    },
    {
        "num": 10, "region": "EUROPE", "topic": "POLITICS",
        "headline": "Mélenchon could win, says justice minister",
        "deck": "The hard-left leader is a plausible president, the minister concedes.",
        "sketch": "paris", "lon": 2.35, "lat": 48.85,
    },
    {
        "num": 11, "region": "MIDDLE EAST", "topic": "GULF",
        "headline": "Saudi Arabia says danger has passed",
        "deck": "All-clear after a Houthi missile was downed.",
        "sketch": "saudi", "lon": 46.7, "lat": 24.7,
    },
    {
        "num": 12, "region": "AFRICA", "topic": "CRIME",
        "headline": "Cocaine and pills seized in eastern Libya",
        "deck": "Officials display a huge drug haul seized in the east.",
        "sketch": "libya", "lon": 20.1, "lat": 32.1,
    },
    {
        "num": 13, "region": "GLOBAL", "topic": "SCIENCE",
        "headline": "Earth's missing billion years are explained",
        "deck": "A Nature study blames mantle currents and ancient ice sheets.",
        "sketch": "geology", "lon": -0.1, "lat": 51.5,
    },
]

# (place, brief, lon, lat, region) — 29 short stories, numbered 14–42.
BRIEFS = [
    ("Gaza", "Israeli tanks cross the Yellow Line", 34.5, 31.5, "MIDDLE EAST"),
    ("Crimea", "Bridge attacked again; traffic halted", 33.5, 45.0, "EUROPE"),
    ("Canberra", "Australia sanctions Israeli settlers", 149.1, -35.3, "OCEANIA"),
    ("Ottawa", "Canada rethinks China ties, seeks US deal", -75.7, 45.4, "AMERICAS"),
    ("New Delhi", "Modi meets the Prince and Princess of Wales", 77.2, 28.6, "ASIA"),
    ("Tokyo", "India and Japan review defence ties", 139.7, 35.7, "ASIA"),
    ("Bengaluru", "Amazon pledges $7bn for renewables", 77.6, 13.0, "ASIA"),
    ("Sydney", "Duckett's 133 puts England on top", 151.2, -33.9, "OCEANIA"),
    ("Auckland", "New Zealand plays GTA VI first", 174.8, -36.8, "OCEANIA"),
    ("Baghdad", "Six French ISIL members jailed for life", 44.4, 33.3, "MIDDLE EAST"),
    ("Nairobi", "Kenya floods kill six as Ruto speaks", 36.8, -1.3, "AFRICA"),
    ("Washington", "Senators warn AI cyber threats grow", -77.0, 38.9, "AMERICAS"),
    ("Mexico City", "Banxico cuts rates to 6.25% on 3–2 vote", -99.1, 19.4, "AMERICAS"),
    ("Seoul", "551,864 sit Korea's college exam", 127.0, 37.5, "ASIA"),
    ("London", "National Grid debunks viral blackout post", -0.1, 51.5, "EUROPE"),
    ("Madrid", "General strike disrupts ports", -3.7, 40.4, "EUROPE"),
    ("Prague", "Crowds demand media freedom", 14.4, 50.1, "EUROPE"),
    ("Jerusalem", "Eisenkot tapped to lead government", 35.2, 31.8, "MIDDLE EAST"),
    ("Caracas", "Hegseth signs US–Venezuela deal", -66.9, 10.5, "AMERICAS"),
    ("Manama", "Bapco refinery back on its feet", 50.6, 26.2, "MIDDLE EAST"),
    ("Riyadh", "Gulf leaders urge Trump: no Iran strike", 46.7, 24.7, "MIDDLE EAST"),
    ("Washington", "Vance: no 'forever war' in the Gulf", -77.0, 38.9, "AMERICAS"),
    ("Sacramento", "California braces for atmospheric river", -121.5, 38.6, "AMERICAS"),
    ("La Paz", "Bolivia declares El Niño emergency", -68.1, -16.5, "AMERICAS"),
    ("Chisinau", "Moldova summons Russian envoy", 28.8, 47.0, "EUROPE"),
    ("Mogadishu", "Somalia accuses UAE of secret bases", 45.3, 2.0, "AFRICA"),
    ("Frankfurt", "Deutsche Bank's $582m Epstein deals", 8.7, 50.1, "EUROPE"),
    ("Kuala Lumpur", "Malaysia's GDP grows 5.5% in Q3", 101.7, 3.1, "ASIA"),
    ("Jakarta", "Bank Indonesia lifts rate to 6%", 106.8, -6.2, "ASIA"),
]

# Big-number strip under the region strip: (big figure, caption)
FIGURES = [
    ("$81.3bn", "largest IPO on record"),
    ("15.9m", "GTA VI pre-orders banked"),
    ("200,000", "evacuated ahead of Akvan"),
    ("$120bn", "COP31 adaptation finance"),
    ("730,000", "Rohingya who fled in 2017"),
    ("13 yrs", "wait since GTA V ended"),
]

# Stories first reported earlier, kept OUT of Thursday's count:
DATE_CHECK = (
    "DATE CHECK — first reported Wednesday 18 November, so not on this page "
    "as news: the EU's proposed €45bn loan for Ukraine · Voyager 1 crossing "
    "one light-day, at 10:16 GMT Wednesday · the House Democrats' 251–11 vote "
    "nominating Hakeem Jeffries · Pew's projection that Islam becomes the "
    "largest religion by 2035 · the first COP31 draft (Monday) · Gogh's record "
    "$190.4m sale in New York · Petrolia's Alaska win."
)

TOTAL_STORIES = len(FEATURED) + len(BRIEFS)  # 42

# ---- page composition -----------------------------------------------------

LAYOUT = {
    "lead_x": (MARGIN, 353, 684),
    "lead_w": 318,
    "lead_y": 176,
    "lead_ill": 88,
    "mid_x": (MARGIN, 220, 419, 617, 816),
    "mid_w": 186,
    "row1_y": 394,
    "row2_y": 543,
    "mid_ill": 58,
    "bottom_y": 692,
    "map_box": (MARGIN, 710, 320, 180),
    "date_y": 946,
    "footer_y": 990,
    "rule_y": 388,
}


def region_counts():
    """Count stories per strip tab from FEATURED + BRIEFS."""
    counts = {}
    for story in FEATURED:
        counts[story["region"]] = counts.get(story["region"], 0) + 1
    for _p, _t, _lo, _la, region in BRIEFS:
        counts[region] = counts.get(region, 0) + 1
    out = []
    for label, regions, tint in STRIP:
        out.append((label, sum(counts.get(r, 0) for r in regions), tint))
    return out


def draw_masthead(pg):
    kicker = face("sans-bold", 13)
    pg.caps(MARGIN, 10, "THE DAILY GLOBE", kicker, PAL["ruby"])
    right = "THURSDAY'S NEWS · ONE PAGE · 42 STORIES"
    rw = pg.caps_width(right, kicker)
    pg.caps(W - MARGIN - rw, 10, right, kicker, PAL["ruby"])
    pg.text((MARGIN, 30), "Thursday 19 November 2026",
            face("serif-bold", 48), PAL["ink"])
    pg.text((MARGIN, 84),
            "Three leaders meet in Shenzhen · A court rules on Myanmar · "
            "The biggest IPO ever debuts",
            face("serif-italic", 14), PAL["ruby"])
    pg.rect((0, 104, W, 107), fill=PAL["pine"])
    pg.rect((0, 107, W, 109), fill=PAL["gilt"])


def draw_region_strip(pg):
    y0, y1 = 113, 129
    counts = region_counts()
    total = sum(c for _l, c, _t in counts)
    assert total == TOTAL_STORIES, f"region strip sums to {total}, not {TOTAL_STORIES}"
    x = MARGIN
    cell = INNER / len(counts)
    for label, n, tint in counts:
        pg.fillbox((x, y0, cell - 2, y1 - y0), tint)
        pg.caps(x + 6, y0 + 3, f"{label} {n}", face("sans-bold", 10),
                PAL["white"])
        x += cell


def draw_figures(pg):
    y0 = 133
    pg.line([(MARGIN, y0 - 3), (W - MARGIN, y0 - 3)], fill=PAL["rule"])
    col_w = INNER / len(FIGURES)
    x = MARGIN
    for big, cap in FIGURES:
        pg.text((x, y0), big, face("serif-bold", 19), PAL["ruby"])
        pg.text((x, y0 + 24), cap, face("sans", 9.5), PAL["deck"])
        x += col_w
    pg.line([(MARGIN, y0 + 38), (W - MARGIN, y0 + 38)], fill=PAL["rule"])


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
    pg.para(x, hy, lines, head, PAL["ink"], 27)
    dy = hy + 27 * len(lines) + 4
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
    pg.para(x, hy, lines, head, PAL["ink"], 16)
    dy = hy + 16 * len(lines) + 2
    deck = face("sans", 10.5)
    dlines = pg.wrap(story["deck"], deck, LAYOUT["mid_w"], 2)
    pg.para(x, dy, dlines, deck, PAL["deck"], 12.5)


def draw_bottom(pg):
    by = LAYOUT["bottom_y"]
    pg.text((MARGIN, by), "WHERE IT HAPPENED", face("sans-bold", 11), PAL["ink"])
    map_box = LAYOUT["map_box"]
    draw_atlas(pg, map_box, FEATURED, BRIEFS)
    pg.rect((map_box[0], map_box[1], map_box[0] + map_box[2],
             map_box[1] + map_box[3]), outline=PAL["rule"])
    legend = [[("Americas", (34, 120, 60)), ("Europe", (36, 84, 160)),
               ("Africa", (176, 110, 32)), ("Middle East", (178, 34, 34))],
              [("Asia", (176, 132, 20)), ("Oceania", (14, 106, 106)),
               ("Global", (110, 70, 150))]]
    for ri, row in enumerate(legend):
        ly = map_box[1] + map_box[3] + 6 + ri * 12
        lx = MARGIN
        for name, tint in row:
            pg.disc(lx + 3.5, ly + 5.5, 3.5, tint)
            pg.text((lx + 10, ly), name, face("sans", 9), PAL["ink"])
            lx += 10 + pg.width(name, face("sans", 9)) + 8
    pg.text((MARGIN, map_box[1] + map_box[3] + 32),
            "Numbered pins: stories 1–13 · dots: briefs 14–42.",
            face("sans", 9), PAL["slate"])
    ax = 362
    pg.text((ax, by), "ALSO ON THURSDAY 19 NOVEMBER — 29 MORE STORIES",
            face("sans-bold", 11), PAL["ink"])
    col_x = [ax, ax + 206, ax + 412]
    col_w = 198
    body = face("sans", 9.5)
    numf = face("sans-bold", 9.5)
    placef = face("sans-bold", 9.5)
    for i, item in enumerate(BRIEFS):
        col = i // 10
        row = i % 10
        x = col_x[col]
        y = by + 18 + row * 23
        place, text = item[0], item[1]
        num = str(14 + i)
        pg.text((x, y), num, numf, PAL["ruby"])
        nx = x + pg.width(num + " ", numf)
        first = f"{place} — {text}"
        lines = pg.wrap(first, body, col_w - (nx - x), 2)
        # place in bold on the first line, rest in regular
        pg.text((nx, y), place + " — ", placef, PAL["ink"])
        rest = text
        px = nx + pg.width(place + " — ", placef)
        wlines = pg.wrap(rest, body, col_w - (px - x), 2)
        pg.para(px, y, wlines, body, PAL["deck"], 11)
        _ = lines


def draw_date_check(pg):
    y0 = LAYOUT["date_y"]
    pg.rect((MARGIN, y0, W - MARGIN, y0 + 40), outline=PAL["ruby"], width=2)
    f = face("sans", 10)
    lines = pg.wrap(DATE_CHECK, f, INNER - 16, 3)
    pg.para(MARGIN + 8, y0 + 4, lines, f, PAL["ink"], 12)


def draw_footer(pg):
    fy = LAYOUT["footer_y"]
    pg.text((MARGIN, fy),
            "Every story here happened, or was first reported, on Thursday "
            "19 November 2026. Disputed claims are attributed, not stated "
            "as fact.",
            face("sans", 9.5), PAL["slate"])
    pg.text((MARGIN, fy + 12),
            "Sources: Reuters, AP, AFP, BBC, The Hindu, IMD, NASA, ICJ, "
            "Pew. Original drawings.",
            face("sans", 9.5), PAL["slate"])


def build_page():
    pg = Page()
    draw_masthead(pg)
    draw_region_strip(pg)
    draw_figures(pg)
    for story, x in zip(FEATURED[:3], LAYOUT["lead_x"]):
        draw_lead(pg, story, x)
    pg.line([(MARGIN, LAYOUT["rule_y"]), (W - MARGIN, LAYOUT["rule_y"])],
            fill=PAL["rule"])
    for story, x in zip(FEATURED[3:8], LAYOUT["mid_x"]):
        draw_card(pg, story, x, LAYOUT["row1_y"])
    for story, x in zip(FEATURED[8:13], LAYOUT["mid_x"]):
        draw_card(pg, story, x, LAYOUT["row2_y"])
    draw_bottom(pg)
    draw_date_check(pg)
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
        place, text = item[0], item[1]
        w = meter.width(place + " — ", face("sans-bold", 9.5))
        n = len(meter.wrap(text, face("sans", 9.5), 198 - w, 99))
        if n > 2:
            print(f"OVERFLOW also #{14 + i}: {n} lines")
            bad = True
    dc = meter.wrap(DATE_CHECK, face("sans", 10), INNER - 16, 99)
    if len(dc) > 3:
        print(f"OVERFLOW date check: {len(dc)} lines")
        bad = True
    title_w = meter.width("Thursday 19 November 2026", face("serif-bold", 48))
    if title_w > INNER:
        print(f"OVERFLOW masthead title: {title_w:.0f}px")
        bad = True
    counts = region_counts()
    total = sum(c for _l, c, _t in counts)
    if total != TOTAL_STORIES:
        print(f"REGION MISMATCH: strip sums to {total}, stories {TOTAL_STORIES}")
        bad = True
    if len(FEATURED) + len(BRIEFS) != TOTAL_STORIES:
        print("STORY COUNT MISMATCH")
        bad = True
    if not bad:
        print(f"fits: all blocks within their boxes; "
              f"regions={counts} total={TOTAL_STORIES}")
    return not bad


if __name__ == "__main__":
    ok = check_fits()
    page = build_page()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    page.save(out)
    digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
    print(f"wrote {out} sha256={digest} fits_ok={ok}")
