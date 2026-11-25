#!/usr/bin/env python3
"""news-image-20261125 v1 -- front page for Wednesday 25 November 2026.
Stdlib only (os, struct, sys, zlib). Deterministic: same run, same bytes.
Usage: python3 main.py [output.png]   (default: entry.png beside this file)
"""
import os
import struct
import sys
import zlib

W, H = 1024, 1024
PAPER = (246, 241, 227)
INK = (26, 26, 26)
NAVY = (27, 42, 74)
RED = (163, 22, 33)
GREEN = (31, 92, 61)
TAN = (216, 196, 154)
GREY = (96, 96, 90)
WHITE = (255, 255, 255)


# ---------------------------------------------------------------- PNG writer
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(px[y * w * 3:(y + 1) * w * 3])
                   for y in range(h))
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(raw, 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = bytes(c) * (x1 - x0)

    def rect(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.fill(x0, y0, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d2 <= r * r:
                        self.set(xx, yy, c)

    def poly(self, pts, c):
        # scanline fill of a simple polygon
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 chars, '#' = on.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    'c': (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    'f': ("..##.", ".#..#", ".#...", "###..", ".#...", ".#...", ".#..."),
    'g': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'i': (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    'j': (".....", "...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."),
    'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    't': (".#...", ".#...", "###..", ".#...", ".#...", ".#...", "..##."),
    'u': (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    'y': (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#"),
    'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    '—': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '–': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    '+': (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    '×': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    '·': (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    '&': (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '=': (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    '°': (".###.", "#...#", ".###.", ".....", ".....", ".....", "....."),
}

# 'j' and 'y' need an 8th row for descenders; pad every glyph to 8 rows.
FONT8 = {}
for _ch, _g in FONT.items():
    _g = list(_g)
    if len(_g) < 8:
        _g.append(".....")
    FONT8[_ch] = tuple(_g)
FONT = FONT8


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, text, color, bold=False, italic=False):
    cx = x
    for ch in text:
        g = FONT.get(ch)
        if g is None:
            g = FONT['?']
        for r in range(8):
            row = g[r]
            shift = (r // 3) if italic else 0
            for c in range(5):
                if row[c] == '#':
                    bw = s + (1 if bold else 0)
                    cv.fill(cx + c * s + shift, y + r * s, bw, s, color)
        cx += 6 * s
    return cx


def wrap(text, width_px, s):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(t, s) <= width_px:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, width_px, s, text, color, lh=None, bold=False):
    if lh is None:
        lh = 8 * s + 3
    yy = y
    for ln in wrap(text, width_px, s):
        draw_text(cv, x, yy, s, ln, color, bold=bold)
        yy += lh
    return yy


# ---------------------------------------------------------------- data
HEROES = [
    {
        "region": "GLOBAL", "num": "1", "color": NAVY,
        "head": "CIA and spy chiefs hit by cyberattack",
        "body": ("The CIA and the director of national intelligence appear to have been hit by a "
                 "cyberattack affecting classified information, CNN reports. Sources say it is "
                 "unrelated to the earlier FBI database attack."),
        "src": "CNN",
        "art": "lock",
    },
    {
        "region": "TRADE", "num": "2", "color": RED,
        "head": "Trump set to unveil new wave of tariffs",
        "body": ("The Trump administration is poised to release findings of a probe into excess "
                 "factory capacity in 16 trading partners, including China and the EU. New import "
                 "duties on a wide range of goods are expected within days."),
        "src": "Reuters",
        "art": "bars",
    },
    {
        "region": "SPACE", "num": "3", "color": GREEN,
        "head": "NATO vows space defence as Russia eyes orbit",
        "body": ("NATO vows to defend against threats in space after reports that Russia is "
                 "preparing to launch a nuclear-armed satellite, possibly as soon as December "
                 "2026. The alliance calls space a contested domain."),
        "src": "BBC",
        "art": "sat",
    },
]

KPI = [
    ("CIA hit", "CIA + ODNI attack", "CNN"),
    ("16", "new US tariffs", "Reuters"),
    ("-5.3%", "Kospi leads slide", "Reuters"),
    ("30", "Cartagena hostages", "WH News"),
    ("500k", "Russian war dead", "BBC"),
    ("4.9%", "Australia inflation", "Guardian"),
    ("74,746", "Gaza death toll", "WAFA"),
    ("12,000", "Manchester evacuees", "Newsreel"),
]

CARDS = [
    ("4", "Cartagena hostages held",
     "Armed men seize a supermarket in Cartagena after a failed cash-truck robbery, "
     "holding at least 30 people hostage. Five elderly women are released.",
     "WH News"),
    ("5", "Russia's own toll: 500,000 dead",
     "Moscow's own figures show almost 500,000 deaths in the war in Ukraine, the BBC "
     "reports, the first official toll of its kind.",
     "BBC"),
    ("6", "Hamas security chief killed",
     "An Israeli drone strike in Gaza City kills Naim Abu Nahl, head of Hamas's internal "
     "security service, and wounds four others.",
     "BBC"),
    ("7", "Seoul minister quits in exam row",
     "Education minister Choi Kyo-jin resigns over an exam cheating scandal that shocked "
     "the nation, officials say.",
     "WH News"),
    ("8", "Australia signs Solomon pact",
     "Australia and the Solomon Islands sign a security pact naming Australia the primary "
     "security partner and ruling out foreign bases.",
     "AP"),
    ("9", "Nigerian monarch, 92, suspended",
     "Katsina State suspends the Emir of Daura, 92, after a tourist's sexual assault "
     "allegation, which the palace disputes.",
     "BBC"),
    ("10", "Abrego Garcia leaves for Spain",
     "Kilmar Abrego Garcia leaves the US for Spain, ending the deportation battle that "
     "became a symbol of Trump's crackdown.",
     "BBC"),
    ("11", "China lifts first Pakistan astronaut",
     "A Chinese rocket lifts off carrying the first Pakistan astronaut aboard, a milestone "
     "for the two countries' space ties.",
     "BBC"),
    ("12", "Dutch climate targets stand",
     "The Hague Court of Appeal rejects the state's request to suspend work on binding "
     "national climate targets while its appeal proceeds.",
     "NOS"),
    ("13", "Iraq seizes Kurdish oilfields",
     "Iraq's premier orders federal forces to seize oilfields and crossings in Kurdish-run "
     "regions, escalating a long dispute.",
     "Starlit"),
]

LIST = [
    ("14", "Meta car bomb hits office.", "AJ"),
    ("15", "Colombia police base drone attack.", "AJ"),
    ("16", "Storm displaces thousands in Brazil.", "AJ"),
    ("17", "WHO chief visits Cuba.", "AJ"),
    ("18", "Sarkozy and Bruni to face trial.", "BBC"),
    ("19", "Spain divided ahead of election.", "BBC"),
    ("20", "UK braces for energy price cap.", "BBC"),
    ("21", "12,000 evacuated in Manchester.", "Newsreel"),
    ("22", "Australia inflation hits 4.9%.", "Guardian"),
    ("23", "Australia apologises to veterans.", "Reuters"),
    ("24", "Syria landmine toll rises.", "BBC"),
    ("25", "Britain sanctions Houthis.", "Starlit"),
    ("26", "Iran medicine shortage bites.", "DW"),
    ("27", "DR Congo plane missing, rebels claim.", "BBC"),
    ("28", "South African dad ignored by police.", "BBC"),
    ("29", "Cameroon conflict shatters lives.", "BBC"),
    ("30", "Nigeria president hit by cuts too.", "BBC"),
    ("31", "WHO evacuates staff in DR Congo.", "Stockbiz"),
    ("32", "Java mine traps dozens.", "Reuters"),
    ("33", "China AI fakes smear Taiwan race.", "BBC"),
    ("34", "Cost of food rises across India.", "BBC"),
    ("35", "Hasina announces return to Bangladesh.", "NMH"),
    ("36", "Thomas Markle indicted in US.", "BBC"),
    ("37", "Giuliani gets Medal of Freedom.", "Newsreel"),
    ("38", "Nvidia falls 6% as AG dodges probe.", "BBC"),
    ("39", "Trump pardons two turkeys.", "BBC"),
    ("40", "Iowans brace for explosives blast.", "BBC"),
]

LEFT_OUT = [
    ("Huawei guilty verdict", "24 Nov"),
    ("COP31 collapse", "24 Nov"),
    ("Huang back at Nvidia", "24 Nov"),
    ("Senegal AFCON winners", "24 Nov"),
    ("Bolsonaro in ICU", "23 Nov"),
    ("Ukraine sinks Libya ship", "23 Nov"),
    ("Settler arson outcry", "22 Nov"),
    ("Missiles over Poland", "24 Nov"),
    ("Microsoft 'Code Red'", "24 Nov"),
    ("'El Chapo Isidro' trial", "24 Nov v1"),
]

DATE_NOTE = ("The Cartagena hostage crisis began late Tuesday 24 Nov in Colombia, but it was "
             "first reported on 25 Nov in Asia and Europe and was still unfolding on Wednesday "
             "morning. A story counts as 25 Nov when it happened, or was first reported, on "
             "25 Nov in at least one time zone.")


# ---------------------------------------------------------------- art
def draw_lock(cv, x, y, w, h):
    # a laptop screen with a padlock: the CIA cyberattack
    cv.fill(x, y, w, h, NAVY)
    cv.rect(x + 8, y + 8, w - 16, h - 26, WHITE, 2)
    # lock body
    bx, by = x + w // 2 - 14, y + h // 2 - 6
    cv.fill(bx, by, 28, 20, WHITE)
    cv.fill(bx + 5, by - 10, 18, 12, NAVY)
    cv.fill(bx + 5, by - 10, 18, 3, WHITE)
    cv.fill(bx + 12, by + 5, 4, 10, RED)
    cv.circle(bx + 14, by + 4, 3, RED)
    # screen base
    cv.fill(x + w // 2 - 40, y + h - 14, 80, 4, WHITE)


def draw_bars(cv, x, y, w, h):
    # rising bars with a red arrow: the tariff wave
    base = y + h - 10
    bw, gap = 34, 14
    heights = [20, 32, 44, 56]
    for i, hh in enumerate(heights):
        bx = x + 14 + i * (bw + gap)
        cv.fill(bx, base - hh, bw, hh, NAVY if i < 3 else RED)
    cv.line(x + 14, base - 16, x + 14 + 3 * (bw + gap) + bw, base - 62, RED, 3)
    ax, ay = x + 14 + 3 * (bw + gap) + bw, base - 62
    cv.line(ax, ay, ax - 12, ay + 2, RED, 3)
    cv.line(ax, ay, ax - 2, ay + 12, RED, 3)
    draw_text(cv, x + w - 52, y + 2, 2, "%", RED, bold=True)


def draw_sat(cv, x, y, w, h):
    # a satellite over an arc of Earth, with stars
    for sx, sy in ((x + 22, y + 14), (x + w - 30, y + 20), (x + w // 2, y + 10),
                   (x + 40, y + 44), (x + w - 60, y + 46)):
        cv.fill(sx, sy, 3, 3, NAVY)
        cv.fill(sx + 1, sy - 1, 1, 5, NAVY)
        cv.fill(sx - 1, sy + 1, 5, 1, NAVY)
    cx, cy = x + w // 2, y + h // 2 - 10
    cv.fill(cx - 52, cy - 10, 40, 20, NAVY)
    cv.fill(cx - 52, cy - 10, 40, 3, WHITE)
    cv.fill(cx + 12, cy - 10, 40, 20, NAVY)
    cv.fill(cx + 12, cy - 10, 40, 3, WHITE)
    cv.fill(cx - 14, cy - 14, 28, 28, RED)
    cv.fill(cx - 9, cy - 9, 18, 18, WHITE)
    cv.fill(cx - 3, cy - 3, 6, 6, RED)
    cv.line(cx - 11, cy - 14, cx - 24, cy - 28, NAVY, 2)
    cv.circle(cx - 24, cy - 28, 3, NAVY)
    # small Earth, fully inside the art box, bottom right
    cv.circle(x + w - 32, y + h - 16, 12, GREEN)
    cv.circle(x + w - 32, y + h - 16, 12, WHITE, fill=False)
    cv.circle(x + w - 36, y + h - 19, 3, TAN)


# ---------------------------------------------------------------- map
def draw_map(cv, x, y, w, h):
    def P(fx, fy):
        return (x + int(fx * w), y + int(fy * h))
    polys = [
        [(0.03, 0.08), (0.30, 0.02), (0.42, 0.10), (0.36, 0.30), (0.28, 0.48),
         (0.15, 0.45), (0.05, 0.30)],
        [(0.40, 0.02), (0.46, 0.04), (0.44, 0.12), (0.40, 0.10)],
        [(0.28, 0.52), (0.38, 0.55), (0.40, 0.75), (0.33, 0.95), (0.27, 0.80)],
        [(0.50, 0.05), (0.60, 0.03), (0.63, 0.18), (0.55, 0.25), (0.50, 0.15)],
        [(0.48, 0.12), (0.51, 0.13), (0.50, 0.20), (0.48, 0.18)],
        [(0.52, 0.30), (0.64, 0.32), (0.66, 0.55), (0.60, 0.85), (0.54, 0.70),
         (0.50, 0.45)],
        [(0.64, 0.02), (0.95, 0.05), (0.98, 0.30), (0.85, 0.45), (0.70, 0.40),
         (0.64, 0.20)],
        [(0.93, 0.25), (0.96, 0.28), (0.95, 0.40), (0.92, 0.38)],
        [(0.78, 0.55), (0.82, 0.58), (0.80, 0.65), (0.77, 0.62)],
        [(0.82, 0.72), (0.95, 0.75), (0.93, 0.88), (0.83, 0.85)],
        [(0.97, 0.85), (0.99, 0.88), (0.98, 0.95), (0.96, 0.92)],
    ]
    for poly in polys:
        cv.poly([P(fx, fy) for fx, fy in poly], TAN)
    dots = [
        (1, 0.24, 0.26), (2, 0.17, 0.34), (3, 0.53, 0.12), (4, 0.27, 0.58),
        (5, 0.66, 0.10), (6, 0.60, 0.30), (7, 0.90, 0.22), (8, 0.96, 0.78),
        (9, 0.55, 0.48), (10, 0.49, 0.18), (11, 0.82, 0.22),
        (12, 0.58, 0.05), (13, 0.63, 0.26),
    ]
    for n, fx, fy in dots:
        dx, dy = x + int(fx * w), y + int(fy * h)
        cv.circle(dx, dy, 8, NAVY)
        cv.circle(dx, dy, 8, WHITE, fill=False)
        s = str(n)
        tx = dx - text_w(s, 1) // 2
        draw_text(cv, tx, dy - 4, 1, s, WHITE, bold=True)


# ---------------------------------------------------------------- page
def build():
    cv = Canvas(W, H, PAPER)
    cv.rect(5, 5, W - 10, H - 10, NAVY, 2)
    cv.rect(9, 9, W - 18, H - 18, NAVY, 1)

    # masthead
    title = "Wednesday 25 November 2026"
    tw = text_w(title, 6)
    draw_text(cv, (W - tw) // 2, 20, 6, title, NAVY, bold=True)
    sub = "THE WORLD IN ONE DAY"
    draw_text(cv, (W - text_w(sub, 2)) // 2, 72, 2, sub, NAVY, bold=True)
    line = "40 STORIES · 7 REGIONS · AS REPORTED ON WEDNESDAY 25 NOVEMBER 2026"
    draw_text(cv, (W - text_w(line, 1)) // 2, 96, 1, line, RED, bold=True)
    teaser = "CIA hacked · Tariffs loom · NATO eyes space · Asia slides"
    draw_text(cv, (W - text_w(teaser, 2)) // 2, 110, 2, teaser, RED, italic=True)
    cv.hline(12, 132, W - 24, NAVY, 2)

    # KPI strip
    kx, ky, kw, kh = 12, 136, W - 24, 46
    cw = kw // 8
    for i, (big, label, src) in enumerate(KPI):
        cx = kx + i * cw
        draw_text(cv, cx + (cw - text_w(big, 2)) // 2, ky + 2, 2, big, NAVY, bold=True)
        draw_text(cv, cx + (cw - text_w(label, 1)) // 2, ky + 20, 1, label, INK)
        draw_text(cv, cx + (cw - text_w(src, 1)) // 2, ky + kh - 10, 1, src, GREY)
        if i:
            cv.vline(cx, ky + 4, kh - 8, NAVY, 1)
    cv.hline(12, ky + kh, W - 24, NAVY, 2)

    # heroes
    hy, hh = 190, 232
    hw = (W - 24 - 12) // 3
    for i, hero in enumerate(HEROES):
        hx = 12 + i * (hw + 6)
        cv.rect(hx, hy, hw, hh, NAVY, 1)
        cv.fill(hx, hy, hw, 20, hero["color"])
        draw_text(cv, hx + 6, hy + 6, 1, hero["region"], WHITE, bold=True)
        draw_text(cv, hx + hw - 6 - text_w(hero["num"], 1), hy + 6, 1,
                  hero["num"], WHITE, bold=True)
        yy = hy + 26
        yy = draw_para(cv, hx + 6, yy, hw - 12, 2, hero["head"], INK, lh=17, bold=True)
        iy = yy + 4
        art_h = 74
        if hero["art"] == "lock":
            draw_lock(cv, hx + 8, iy, hw - 16, art_h)
        elif hero["art"] == "bars":
            draw_bars(cv, hx + 8, iy, hw - 16, art_h)
        else:
            draw_sat(cv, hx + 8, iy, hw - 16, art_h)
        by = iy + art_h + 6
        draw_para(cv, hx + 6, by, hw - 12, 1, hero["body"], INK, lh=10)
        draw_text(cv, hx + 6, hy + hh - 14, 1, hero["src"], GREY, bold=True)

    # cards, two rows of five
    cy0, ch, gap = 430, 128, 6
    cw2 = (W - 24 - 4 * gap) // 5
    for idx, (num, head, body, src) in enumerate(CARDS):
        row, col = divmod(idx, 5)
        cx = 12 + col * (cw2 + gap)
        cy = cy0 + row * (ch + gap)
        cv.rect(cx, cy, cw2, ch, NAVY, 1)
        yy = cy + 6
        yy = draw_para(cv, cx + 6, yy, cw2 - 12, 2, head, INK, lh=16, bold=True)
        draw_para(cv, cx + 6, yy + 3, cw2 - 12, 1, body, INK, lh=10)
        draw_text(cv, cx + 6, cy + ch - 13, 1, num + " · " + src, GREY, bold=True)

    # bottom: map + list
    by0 = 700
    cv.hline(12, by0 - 6, W - 24, NAVY, 2)
    draw_text(cv, 12, by0, 1, "WHERE IT HAPPENED", NAVY, bold=True)
    draw_map(cv, 12, by0 + 16, 388, 176)
    draw_text(cv, 12, by0 + 196, 1, "Dots mark the 13 featured stories.", GREY)
    lx = 412
    draw_text(cv, lx, by0, 1, "ALSO ON WEDNESDAY 25 NOVEMBER — 27 MORE STORIES",
              NAVY, bold=True)
    col_w = (W - 24 - lx + 12 - 16) // 2
    for j, (num, text, src) in enumerate(LIST):
        col = 0 if j < 14 else 1
        xx = lx + col * (col_w + 16)
        yy = by0 + 16 + (j % 14) * 14
        full = num + ". " + text + " — " + src
        if text_w(full, 1) > col_w:
            while text_w(full + "...", 1) > col_w and len(full) > 4:
                full = full[:-1]
            full = full + "..."
        draw_text(cv, xx, yy, 1, full, INK)

    # DATE CHECK
    dy = 920
    cv.rect(12, dy, W - 24, 78, RED, 2)
    t = "DATE CHECK — WHAT WE LEFT OUT, AND WHAT WAS STILL UNCONFIRMED"
    draw_text(cv, (W - text_w(t, 1)) // 2, dy + 5, 1, t, RED, bold=True)
    draw_text(cv, 20, dy + 19, 1, "THROWN OUT AS OLD NEWS", RED, bold=True)
    for i, (item, when) in enumerate(LEFT_OUT):
        col = 0 if i < 5 else 1
        xx = 20 + col * 250
        yy = dy + 31 + (i % 5) * 9
        draw_text(cv, xx, yy, 1, "× " + item + " — " + when, INK)
    draw_text(cv, 520, dy + 19, 1, "DATE NOTE — WHY ONE STORY COUNTS", RED, bold=True)
    draw_para(cv, 520, dy + 31, W - 24 - 520 - 8, 1, DATE_NOTE, INK, lh=10)
    draw_text(cv, (W - text_w("Every story here happened, or was first reported, "
                               "on Wednesday 25 November 2026 in at least one time zone.",
                               1)) // 2,
              1004, 1,
              "Every story here happened, or was first reported, on Wednesday 25 "
              "November 2026 in at least one time zone.", GREY)
    return cv


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out is None:
        out = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
                           if os.path.isdir(os.environ.get(
                               "MAKEFUN_OUTPUT_DIR", "/output")) else ".",
                           "entry.png")
    cv = build()
    write_png(out, W, H, cv.px)
    print("wrote %s  %d bytes" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    main()
