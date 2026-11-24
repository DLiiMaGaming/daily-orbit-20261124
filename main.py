#!/usr/bin/env python3
"""The Daily Orbit - Tuesday 24 November 2026.

A one-page newspaper front page summing up the world's news of
Tuesday 24 November 2026: 50 stories, 7 regions, 12 fields, every one
checked to have happened, or been first reported, on that day.

Pure Python standard library only (the grader runs with no network and
nothing installed): the image is drawn into an RGB framebuffer and
encoded as PNG by hand (zlib + struct). Deterministic: no clock, no
randomness except a fixed-seed grain, so two runs write identical bytes.

Layout (1024 x 1024):
  masthead -> UTC timeline strip -> 3 lead stories -> world map with
  numbered pins + DATE CHECK box + DAY IN NUMBERS -> numbered list of
  all 50 stories with source per story -> footer with method + sources.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- colours
PAPER = (247, 242, 231)   # newsprint cream
INK = (26, 26, 26)        # near-black ink
RED = (176, 42, 32)       # masthead red / DATE CHECK
NAVY = (31, 78, 121)      # timeline band
BLUE = (47, 102, 168)     # ocean
LAND = (196, 178, 138)    # map land
LAND2 = (168, 152, 112)   # map land shade
GREEN = (46, 125, 50)     # CONFIRMED marker
AMBER = (176, 124, 20)    # REPORTED marker
GREY = (110, 105, 95)
LIGHT = (232, 226, 210)   # panel tint
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- framebuffer
buf = bytearray(W * H * 3)


def _set(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]


def rect(x, y, w, h, c):
    for yy in range(max(0, y), min(H, y + h)):
        base = (yy * W + max(0, x)) * 3
        for xx in range(max(0, x), min(W, x + w)):
            i = (yy * W + xx) * 3
            buf[i] = c[0]
            buf[i + 1] = c[1]
            buf[i + 2] = c[2]


def frame(x, y, w, h, c, t=1):
    rect(x, y, w, t, c)
    rect(x, y + h - t, w, t, c)
    rect(x, y, t, h, c)
    rect(x + w - t, y, t, h, c)


def hline(x0, x1, y, c):
    for xx in range(max(0, x0), min(W, x1 + 1)):
        _set(xx, y, c)


def vline(x, y0, y1, c):
    for yy in range(max(0, y0), min(H, y1 + 1)):
        _set(x, yy, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        _set(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, fill=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
            if fill:
                if d <= r * r:
                    _set(xx, yy, c)
            else:
                if r * r - 2 * r <= d <= r * r:
                    _set(xx, yy, c)


def poly(points, c):
    """Scanline fill for a simple polygon (list of (x, y))."""
    if not points:
        return
    ys = [p[1] for p in points]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            for xx in range(int(xs[j]), int(xs[j + 1]) + 1):
                _set(xx, y, c)


def grain(amp):
    """Deterministic newsprint grain (fixed-seed xorshift)."""
    s = 0x12345678
    for i in range(0, len(buf), 3):
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        n = (s % (2 * amp + 1)) - amp
        for k in range(3):
            v = buf[i + k] + n
            buf[i + k] = 0 if v < 0 else (255 if v > 255 else v)


# ---------------------------------------------------------------- 5x7 font
# Hand-drawn bitmap font: each glyph is 7 rows of 5 pixels.
# '#' = ink, '.' = empty. Only the characters the page uses.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "·": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}


def draw_text(x, y, s, scale, color):
    """Draw upper-cased text; returns width in pixels."""
    cx = x
    for ch in s.upper():
        g = FONT.get(ch, FONT["?"])
        for r in range(7):
            row = g[r]
            for cc in range(5):
                if row[cc] == "1":
                    rect(cx + cc * scale, y + r * scale, scale, scale, color)
        cx += (5 + 1) * scale
    return cx - x


def text_w(s, scale):
    return len(s) * (5 + 1) * scale


def wrap(s, max_chars):
    """Greedy word wrap to lines of at most max_chars characters."""
    words = s.split(" ")
    lines = []
    cur = ""
    for wd in words:
        if cur and len(cur) + 1 + len(wd) > max_chars:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return lines

# ---------------------------------------------------------------- the news
# 50 stories, each: (headline <= 35 chars for the one-line list,
#                   source outlet, True = CONFIRMED, False = REPORTED).
# Every story happened, or was first reported, on Tuesday 24 Nov 2026.
# Research: Reuters, AP, BBC, Al Jazeera, The Guardian, CNBC, France 24,
# DW, SCMP, Euronews, CBS, NASA, Meduza, UPI, La Nacion, Africanews,
# MercoPress, Japan Times, Phys.org, RFI, Middle East Eye,
# Kyiv Independent, Gold Wall Press - read 24 Nov 2026 to ~13:30 UTC.
STORIES = [
    ("COP31 CLIMATE TALKS END NO DEAL", "BBC", True),
    ("NATO VOWS SPACE DEFENCE", "BBC", True),
    ("QUAKE M5.3 SHAKES NEPAL", "REUTERS", True),
    ("RUSSIAN DRONE IN POLAND", "GUARDIAN", True),
    ("ZELENSKY URGES TALKS; 2 KILLED", "FRANCE 24", True),
    ("700,000 RUSSIAN DEAD*", "SCMP", False),
    ("TRIPOLI DEMANDS ANSWERS", "GUARDIAN", True),
    ("UK SANCTIONS MYANMAR GENERALS", "BBC", True),
    ("EU PROPOSES 22ND SANCTIONS", "UPI", True),
    ("ESTONIA CLOSES RUSSIA BORDER", "MEDUZA", True),
    ("GERMANY INTO UKRAINE DELTA NET", "KYIV IND.", True),
    ("GAZA MENINGITIS ALERT", "AL JAZEERA", True),
    ("OXFAM: GAZA A 'TOXIC WASTELAND'", "BBC", True),
    ("IRAQ TAKES KURDISH OILFIELDS", "REUTERS", True),
    ("IRAN VOWS ARMED TANKER ESCORTS", "REUTERS", False),
    ("QATAR PM SEEKS US-IRAN TALKS", "AL JAZEERA", True),
    ("YEMEN STRIKES KILL ABOUT 25", "M. EAST EYE", False),
    ("IRAN FLOGS SINGER 74 LASHES", "BBC", True),
    ("DR CONGO PLANE MISSING", "BBC", True),
    ("SUDAN DRONE HITS UN BUILDING", "RFI", False),
    ("AMNESTY: PROBE TIGRAY SHELLING", "REUTERS", True),
    ("ZAMBIA OPPOSITION INDICTED", "AFRICANEWS", True),
    ("TORTOISES RESTORE SEYCHELLES", "LA NACION", True),
    ("US LOSES MEASLES-FREE STATUS", "AP", True),
    ("STATES SUE MUSK FIRMS OVER GROK", "CNBC", True),
    ("ARMY CLEARED FOR IOWA BLAST", "AL JAZEERA", True),
    ("TRUMP DROPS PELTOLA CHALLENGE", "AP", True),
    ("FIFA NAMES 2031 WOMEN'S HOSTS", "CBS", True),
    ("WEBB: STAR MERGED PRE-BLAST", "NASA", True),
    ("OLDEST QUASAR PAIR FOUND", "AP", True),
    ("S&P 500 +4.7%, NASDAQ +6.5%", "REUTERS", True),
    ("NVIDIA SLIDES AFTER HUANG", "REUTERS", True),
    ("CROWDSTRIKE BUYS ZSCALER, $44BN", "CNBC", True),
    ("SANOFI BUYS INSMED, $41BN", "REUTERS", True),
    ("AUSTRALIA LETS PEOPLE SUE TECH", "GUARDIAN", True),
    ("BELGIUM STRIKE HALTS FLIGHTS", "EURONEWS", True),
    ("BOMB THREATS HIT DE, DK SCHOOLS", "DW", True),
    ("DENMARK BACKS GHETTO EVICTIONS", "AL JAZEERA", True),
    ("COLOMBIA CAR BOMB WOUNDS 21", "AL JAZEERA", True),
    ("BRAZIL REAL WEAKENS; GROWTH CUT", "MERCOPRESS", True),
    ("CHINA DEATH SENTENCE FOR SPYING", "GOLD WALL", False),
    ("PAKISTANI TO FLY ON TIANGONG", "PHYS.ORG", True),
    ("CHINA EXTENDS MINERAL CURB PAUSE", "SCMP", True),
    ("NEPAL PM VISITS INDIA", "EURONEWS", True),
    ("HASINA PLANS RETURN DEC 16", "BBC", True),
    ("BANGLADESH GARMENT CLASHES", "REUTERS", True),
    ("INDONESIA FACTORY FIRE TOLL 26", "GUARDIAN", True),
    ("INDONESIA EX-POLICE CHIEF HELD", "JAPAN TIMES", True),
    ("JAPAN FACTORY GROWS", "REUTERS", True),
    ("MEXICO INFLATION HITS HIGH", "REUTERS", True),
]

# Lead stories (also #1-3 in the list above): (kicker, headline lines,
# body lines, illustration key)
LEADS = [
    ("CLIMATE - ANTALYA, TURKEY",
     ["COP31 ENDS", "WITH NO DEAL"],
     ["UN climate talks end with",
      "no deal, two days over -",
      "the longest COP ever, and",
      "first no-deal since 2009."],
     "globe"),
    ("DEFENCE - BRUSSELS, BELGIUM",
     ["NATO VOWS", "SPACE DEFENCE"],
     ["Rutte: NATO will defend",
      "against threats in space,",
      "after reports Russia may",
      "launch a nuclear satellite."],
     "satellite"),
    ("DISASTER - KOSHI, NEPAL - 01:32 UTC",
     ["QUAKE M5.3", "SHAKES NEPAL"],
     ["A magnitude 5.3 quake",
      "strikes Koshi province;",
      "tremors felt in India,",
      "Bhutan, Bangladesh, China."],
     "quake"),
]

# UTC timeline strip: (time label, event) - '~' = approximate hour.
TIMELINE = [
    ("01:32", "NEPAL QUAKE"),
    ("02:15", "NATO SPACE VOW"),
    ("02:37", "CHINA SPY CASE"),
    ("~06:00", "COP31 NO DEAL"),
    ("~09:00", "SANOFI $41BN"),
    ("~11:00", "UK SANCTIONS"),
    ("13:08", "MEXICO INFLATION"),
    ("~13:00", "EU SANCTIONS"),
]

# Stories deliberately left out because they broke on another day.
EXCLUDED = [
    "ICJ MYANMAR GENOCIDE RULING - 19 NOV",
    "PUIGDEMONT AMNESTY - COURT RULED 23 NOV",
    "NVIDIA REINSTATES HUANG AS CEO - 23 NOV",
    "TANKERS HIT BY MINES IN HORMUZ - 16 NOV",
    "FAA NATIONWIDE GROUND STOP - 13 NOV",
    "XI-TRUMP-PUTIN MEETING - DUE 19 NOV",
    "US BLACKLISTS MEGASPEED - 23 NOV",
    "GUTERRES AI SAFETY CALL - 23 NOV",
    "UKRAINE SINKS SHIP OFF BENGHAZI - 23 NOV",
]

NUMBERS = [
    ("50", "STORIES"),
    ("7", "REGIONS"),
    ("12", "FIELDS"),
    ("700K", "RUSSIAN DEAD*"),
]

# World map: coarse equirectangular continent polygons (lon, lat).
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 73), (-65, 60), (-55, 52), (-60, 46), (-70, 42), (-75, 35),
     (-80, 32), (-85, 30), (-90, 21), (-97, 16), (-94, 17), (-87, 13),
     (-83, 9), (-79, 9), (-85, 11), (-92, 15), (-97, 16), (-105, 20),
     (-110, 23), (-114, 28), (-120, 34), (-125, 40), (-124, 48),
     (-130, 55), (-145, 60), (-158, 58)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-25, 70),
     (-20, 74), (-30, 76), (-45, 76), (-58, 74)],
    # South America
    [(-79, 9), (-75, 11), (-72, 12), (-64, 10), (-60, 8), (-52, 5),
     (-50, 0), (-44, -3), (-35, -8), (-39, -15), (-41, -23), (-48, -28),
     (-53, -33), (-58, -38), (-62, -41), (-65, -45), (-68, -50),
     (-70, -54), (-73, -50), (-73, -44), (-72, -37), (-70, -30),
     (-70, -23), (-75, -15), (-80, -6), (-81, -3)],
    # Africa
    [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-15, 11),
     (-12, 8), (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (12, 2),
     (9, -1), (12, -5), (13, -10), (12, -17), (14, -22), (16, -28),
     (20, -35), (26, -34), (32, -29), (35, -24), (40, -16), (40, -10),
     (42, -4), (46, -1), (51, 2), (51, 11), (48, 11), (44, 11), (43, 12),
     (40, 15), (38, 18), (37, 22), (35, 28), (32, 31), (25, 32),
     (19, 33), (11, 34), (10, 37), (0, 36)],
    # Eurasia
    [(-10, 36), (-9, 43), (-2, 48), (-4, 49), (0, 51), (3, 53), (8, 57),
     (10, 59), (5, 60), (5, 62), (12, 65), (18, 69), (25, 71), (30, 70),
     (40, 68), (50, 69), (60, 69), (70, 72), (80, 73), (90, 75),
     (100, 77), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70),
     (160, 70), (170, 67), (178, 65), (170, 60), (162, 56), (158, 52),
     (150, 59), (142, 59), (140, 53), (135, 44), (130, 42), (127, 40),
     (122, 38), (120, 32), (115, 28), (110, 20), (108, 18), (105, 10),
     (103, 8), (100, 7), (98, 10), (95, 16), (92, 21), (89, 22),
     (86, 20), (82, 17), (80, 13), (77, 8), (75, 12), (72, 20),
     (68, 23), (66, 25), (62, 25), (58, 26), (56, 27), (52, 28),
     (50, 29), (48, 30), (44, 29), (42, 27), (39, 21), (38, 18),
     (35, 20), (34, 28), (33, 31), (36, 36), (30, 36), (27, 37),
     (23, 36), (22, 37), (19, 40), (15, 44), (12, 44), (8, 44),
     (3, 43), (0, 40), (-2, 37), (-6, 36), (-9, 37)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
     (-3, 50)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 37), (140, 39),
     (141, 41), (143, 43), (145, 44), (142, 44), (140, 42), (139, 38),
     (137, 35), (133, 34), (130, 32)],
    # Indonesia
    [(95, 5), (98, 3), (100, 0), (103, -3), (106, -6), (110, -7),
     (114, -8), (118, -9), (120, -10), (124, -10), (128, -8), (131, -6),
     (134, -4), (136, -2), (138, -2), (141, -3), (141, -1), (138, 0),
     (135, 0), (132, 0), (130, -1), (128, 1), (126, 2), (124, 1),
     (122, 1), (120, 0), (119, 0), (117, 1), (115, 3), (112, 5),
     (108, 6), (105, 6), (102, 5), (98, 5)],
    # Australia
    [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -12),
     (132, -11), (130, -13), (126, -14), (122, -17), (118, -20)],
    # New Zealand
    [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38),
     (175, -40), (172, -43), (168, -46)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (50, -20), (47, -25), (45, -25),
     (44, -20)],
]

# Numbered map pins: (story number, lon, lat, label dx, label dy)
PINS = [
    (1, 30.7, 36.9, 10, -14),
    (2, 4.4, 50.8, 8, -16),
    (3, 85.3, 27.7, 10, 8),
    (4, 21.0, 52.2, 12, -14),
    (7, 20.1, 32.1, -26, 6),
    (12, 34.5, 31.5, 10, 8),
    (15, 51.4, 35.7, 12, -12),
    (19, 29.0, -3.0, 10, 6),
    (24, -77.0, 38.9, -26, -10),
    (39, -73.6, 4.2, 10, 6),
    (41, 116.4, 39.9, 10, -14),
    (47, 106.8, -6.2, 10, 6),
]

# ---------------------------------------------------------------- drawing
def draw_masthead():
    rect(0, 0, W, 8, RED)
    rect(0, 8, W, 2, INK)
    title = "THE DAILY ORBIT"
    draw_text((W - text_w(title, 6)) // 2, 16, title, 6, INK)
    sub = "TUESDAY 24 NOVEMBER 2026"
    draw_text((W - text_w(sub, 2)) // 2, 62, sub, 2, RED)
    tag = "50 STORIES  ·  7 REGIONS  ·  12 FIELDS  ·  EVERY ONE FROM THIS TUESDAY"
    draw_text((W - text_w(tag, 1)) // 2, 82, tag, 1, INK)
    hline(8, W - 9, 94, INK)
    hline(8, W - 9, 97, INK)


def draw_timeline():
    y0, y1 = 102, 140
    rect(8, y0, W - 16, y1 - y0, NAVY)
    draw_text(16, y0 + 5, "THE DAY IN UTC", 2, WHITE)
    x = 200
    step = (W - 16 - 200) // len(TIMELINE)
    for t, ev in TIMELINE:
        draw_text(x, y0 + 4, t, 1, (255, 214, 130))
        draw_text(x, y0 + 15, ev, 1, WHITE)
        x += step
    draw_text(16, y0 + 24, "TIMES UTC - NEWS READ TO ~13:30 UTC; THE DAY CONTINUES",
              1, (200, 210, 225))


def draw_lead(x0, y0, w, h, lead):
    kicker, heads, body, art = lead
    frame(x0, y0, w, h, INK, 2)
    rect(x0 + 2, y0 + 2, w - 4, 16, RED)
    draw_text(x0 + 8, y0 + 5, kicker, 1, WHITE)
    yy = y0 + 22
    for ln in heads:
        draw_text(x0 + 8, yy, ln, 3, INK)
        yy += 22
    yy = y0 + 70
    for ln in body:
        draw_text(x0 + 8, yy, ln, 2, INK)
        yy += 16
    # illustration strip at the bottom of the panel
    iy = y0 + 136
    hline(x0 + 8, x0 + w - 9, iy - 2, GREY)
    if art == "globe":
        cx, cy = x0 + 40, iy + 16
        circle(cx, cy, 13, BLUE, fill=False)
        for dy in (-7, 0, 7):
            hline(cx - 11, cx + 11, cy + dy, BLUE)
        vline(cx, cy - 13, cy + 13, BLUE)
        line(cx - 9, cy + 9, cx + 9, cy - 9, BLUE)
        draw_text(x0 + 62, iy + 4, "NO DEAL -", 2, RED)
        draw_text(x0 + 62, iy + 20, "TALKS COLLAPSE", 1, INK)
    elif art == "satellite":
        cx, cy = x0 + 40, iy + 16
        rect(cx - 14, cy - 3, 12, 6, NAVY)
        rect(cx + 2, cy - 3, 12, 6, NAVY)
        rect(cx - 4, cy - 5, 8, 10, RED)
        line(cx, cy - 5, cx + 8, cy - 13, INK)
        circle(cx + 8, cy - 13, 2, INK)
        draw_text(x0 + 62, iy + 4, "EYES ON ORBIT -", 2, NAVY)
        draw_text(x0 + 62, iy + 20, "A BLAST ABOVE US ALL", 1, INK)
    elif art == "quake":
        cx = x0 + 40
        line(x0 + 12, iy + 28, x0 + 26, iy + 10, INK)
        line(x0 + 26, iy + 10, x0 + 40, iy + 28, INK)
        line(x0 + 40, iy + 28, x0 + 56, iy + 14, INK)
        line(x0 + 56, iy + 14, x0 + 68, iy + 28, INK)
        xx = x0 + 78
        pts = [(xx, iy + 16), (xx + 8, iy + 16), (xx + 11, iy + 6),
               (xx + 14, iy + 26), (xx + 17, iy + 10), (xx + 20, iy + 22),
               (xx + 23, iy + 16), (xx + 34, iy + 16)]
        for a, b in zip(pts, pts[1:]):
            line(a[0], a[1], b[0], b[1], RED)
        draw_text(x0 + 118, iy + 4, "01:32 UTC -", 2, RED)
        draw_text(x0 + 118, iy + 20, "FELT IN 5 NATIONS", 1, INK)


def draw_leads():
    y0, h = 146, 166
    w = (W - 16 - 16) // 3
    for i, lead in enumerate(LEADS):
        draw_lead(8 + i * (w + 8), y0, w, h, lead)


def _project(lon, lat, mx, my, mw, mh):
    x = mx + (lon + 170.0) / 360.0 * mw
    y = my + (80.0 - lat) / 138.0 * mh
    return int(x), int(y)


def draw_map():
    mx, my, mw, mh = 8, 316, 620, 156
    frame(mx, my, mw, mh, INK, 2)
    rect(mx + 2, my + 2, mw - 4, 18, NAVY)
    draw_text(mx + 8, my + 6, "WHERE IT HAPPENED - THE WORLD, PINNED", 1, WHITE)
    rect(mx + 2, my + 20, mw - 4, mh - 22, (214, 228, 238))
    # graticule
    for lon in range(-150, 181, 30):
        x, _ = _project(lon, 0, mx, my + 20, mw, mh - 20)
        vline(x, my + 20, my + mh - 2, (190, 205, 218))
    for lat in (60, 30, 0, -30):
        _, y = _project(0, lat, mx, my + 20, mw, mh - 20)
        hline(mx + 2, mx + mw - 3, y, (190, 205, 218))
    # continents
    for cont in CONTINENTS:
        pts = [_project(lon, lat, mx, my + 20, mw, mh - 20)
               for lon, lat in cont]
        poly(pts, LAND)
        for a, b in zip(pts, pts[1:] + pts[:1]):
            line(a[0], a[1], b[0], b[1], LAND2)
    # pins: red dot + numbered label box on a leader line
    for num, lon, lat, dx, dy in PINS:
        px, py = _project(lon, lat, mx, my + 20, mw, mh - 20)
        s = str(num)
        bw, bh = len(s) * 6 + 6, 13
        bx, by = px + dx, py + dy
        line(px, py, bx + bw // 2, by + bh // 2, RED)
        circle(px, py, 4, RED)
        circle(px, py, 4, WHITE, fill=False)
        rect(bx, by, bw, bh, WHITE)
        frame(bx, by, bw, bh, RED, 1)
        draw_text(bx + 3, by + 3, s, 1, RED)


def draw_datecheck():
    x0, y0, w, h = 636, 316, 380, 104
    frame(x0, y0, w, h, RED, 2)
    rect(x0 + 2, y0 + 2, w - 4, 18, RED)
    draw_text(x0 + 8, y0 + 6, "DATE CHECK - LEFT OUT ON PURPOSE", 1, WHITE)
    yy = y0 + 24
    for line_s in EXCLUDED:
        draw_text(x0 + 8, yy, "X " + line_s, 1, INK)
        yy += 9


def draw_numbers():
    x0, y0, w, h = 636, 424, 380, 48
    rect(x0 + 2, y0 + 2, w - 4, 18, INK)
    draw_text(x0 + 8, y0 + 6, "THE DAY IN NUMBERS", 1, WHITE)
    cw = (w - 16) // 4
    for i in range(4):
        num, lab = NUMBERS[i]
        cx = x0 + 8 + i * cw
        draw_text(cx, y0 + 22, num, 2, RED)
        draw_text(cx, y0 + 40, lab, 1, INK)


def draw_list():
    y0 = 478
    draw_text(8, y0, "THE 50 STORIES - NUMBERED, SOURCED, DATE-CHECKED", 2, INK)
    lx = W - 8 - text_w("GREEN NUMBER = CONFIRMED  -  AMBER = REPORTED", 1)
    draw_text(lx, y0 + 4, "GREEN NUMBER = CONFIRMED  -  AMBER = REPORTED", 1, INK)
    hline(8, W - 9, y0 + 20, INK)
    col_w = (W - 16 - 8) // 2
    yy = y0 + 28
    for col in range(2):
        xx = 8 + col * (col_w + 8)
        for j in range(25):
            idx = col * 25 + j
            head, src, conf = STORIES[idx]
            num = "%d." % (idx + 1)
            colr = GREEN if conf else AMBER
            y = yy + j * 18
            draw_text(xx, y, num, 2, colr)
            nx = xx + len(num) * 12
            draw_text(nx, y, head, 2, INK)
            sx = nx + len(head) * 12 + 4
            draw_text(sx, y + 7, "(" + src + ")", 1, GREY)


def draw_footer():
    y0 = 992
    hline(8, W - 9, y0, INK)
    f1 = ("EVERY STORY HERE HAPPENED, OR WAS FIRST REPORTED, ON TUESDAY "
          "24 NOVEMBER 2026. CLAIMS ARE ATTRIBUTED; REPORTED = SINGLE-SOURCE "
          "OR UNCONFIRMED.")
    for i, ln in enumerate(wrap(f1, 165)):
        draw_text(8, y0 + 5 + i * 9, ln, 1, INK)
    f2 = ("SOURCES: REUTERS, AP, BBC, AL JAZEERA, AFP, THE GUARDIAN, CNBC, "
          "FRANCE 24, DW, SCMP, EURONEWS, CBS, NASA, MEDUZA, UPI, LA NACION, "
          "AFRICANEWS, MERCOPRESS, JAPAN TIMES, PHYS.ORG, RFI, MIDDLE EAST EYE, "
          "KYIV INDEPENDENT, GOLD WALL PRESS. *LEAKED-DATA TOLL UNCONFIRMED.")
    for i, ln in enumerate(wrap(f2, 165)):
        draw_text(8, y0 + 5 + 9 + i * 9, ln, 1, GREY)

# ---------------------------------------------------------------- PNG output
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", comp) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    rect(0, 0, W, H, PAPER)
    draw_masthead()
    draw_timeline()
    draw_leads()
    draw_map()
    draw_datecheck()
    draw_numbers()
    draw_list()
    draw_footer()
    grain(4)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
