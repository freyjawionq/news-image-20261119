#!/usr/bin/env python3
"""The 19 November 2026 world-news front page, drawn in pure Python.

A small hand-rolled renderer: a 5x7 bitmap typeface, a word wrapper and a
PNG writer built on zlib/struct only. No network, no files read, no clock:
the picture is a pure function of the STORIES table below, so every run
writes exactly the same bytes.

Run:  MAKEFUN_OUTPUT_DIR=<dir> python3 main.py   (writes <dir>/entry.png)
"""

import binascii
import os
import struct
import zlib

# --------------------------------------------------------------------------
# 5x7 bitmap typeface. Each glyph is seven rows of five pixels; '#' is ink.
# --------------------------------------------------------------------------

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "#.#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
}

# --------------------------------------------------------------------------
# The day's stories. Every line is mapped to a dated source in SOURCES.md.
# --------------------------------------------------------------------------

DATE_LINE = "THURSDAY 19 NOVEMBER 2026"
PAPER_NAME = "THE WORLD IN ONE PAGE"

LEAD = {
    "kicker": "SHENZHEN - APEC SUMMIT",
    "headline": "TRUMP, XI AND PUTIN SET TO MEET FACE TO FACE IN SHENZHEN",
    "sub": (
        "THREE-WAY SUMMIT OF THE US, CHINESE AND RUSSIAN LEADERS DUE "
        "THURSDAY AT THE APEC FORUM. NUCLEAR ARMS CUTS AND IRAN ON THE "
        "TABLE - EUROPE ABSENT."
    ),
}

PANELS = [
    {
        "kicker": "BERLIN - UKRAINE DIPLOMACY",
        "headline": "UKRAINE'S ALLIES SET TO CONVENE IN BERLIN",
        "sub": (
            "GERMANY, FRANCE, BRITAIN, POLAND AND ITALY, WITH NATO'S RUTTE, "
            "DUE TO MEET TRUMP ENVOYS WITKOFF AND KUSHNER OVER GUARANTEES "
            "FOR KYIV."
        ),
    },
    {
        "kicker": "TOKYO - INDIA AND JAPAN",
        "headline": "INDIA AND JAPAN SET FOR 2+2 TALKS IN TOKYO",
        "sub": (
            "RAJNATH SINGH AND S JAISHANKAR TO MEET KOIZUMI AND MOTEGI FOR "
            "THE FOURTH 2+2 DIALOGUE, ON DEFENCE AND THE INDO-PACIFIC."
        ),
    },
    {
        "kicker": "SUVA - CLIMATE",
        "headline": "FIJI DECLARES DISASTER",
        "sub": (
            "EL NINO DROUGHT BRINGS WATER SHORTAGES. A ONE-MONTH STATE OF "
            "DISASTER; FJ$20M FOR EMERGENCY WATER."
        ),
    },
    {
        "kicker": "ANTALYA - COP31",
        "headline": "COP31 DEAL STILL ELUSIVE",
        "sub": (
            "AS OF WEDNESDAY'S TALKS: NEW DRAFT TEXTS DUE EARLY THURSDAY; "
            "21 ISSUES UNRESOLVED, MINISTERS DEADLOCKED OVER FINANCE."
        ),
    },
    {
        "kicker": "CULTURE - GAMES",
        "headline": "GTA VI ARRIVES AT LAST",
        "sub": (
            "GRAND THEFT AUTO VI, AFTER A 13-YEAR WAIT, IS PLAYABLE FROM "
            "MIDNIGHT LOCAL TIME ON PS5 AND XBOX."
        ),
    },
]

FOOTER = "ONE DAY, ONE PAGE - THE EVENTS OF 19 NOVEMBER 2026, FROM REPORTING PUBLISHED ON OR AROUND THAT DATE; SOURCES IN SOURCES.MD"

# --------------------------------------------------------------------------
# Canvas: a flat RGB pixel buffer with rectangle and text primitives.
# --------------------------------------------------------------------------

WIDTH = 1024
HEIGHT = 768

PAPER = (246, 241, 230)
INK = (24, 24, 32)
ACCENT = (164, 38, 44)
NAVY = (30, 62, 110)
GREY = (96, 96, 104)
RULE = (24, 24, 32)
PANEL_BG = (252, 249, 242)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(rgb)

    def rect(self, x, y, w, h, rgb):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, rgb)

    def frame(self, x, y, w, h, rgb, thick=2):
        self.rect(x, y, w, thick, rgb)
        self.rect(x, y + h - thick, w, thick, rgb)
        self.rect(x, y, thick, h, rgb)
        self.rect(x + w - thick, y, thick, h, rgb)


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, rgb):
    """Draw text with the top-left of the first glyph at (x, y)."""
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    cv.rect(cx + col_i * scale, y + row_i * scale, scale, scale, rgb)
        cx += 6 * scale
    return cx - scale


def draw_centered(cv, y, text, scale, rgb):
    x = (cv.w - text_width(text, scale)) // 2
    return draw_text(cv, x, y, text, scale, rgb)


def wrap(text, scale, max_width):
    """Greedy word wrap: returns the lines that fit max_width pixels."""
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_block(cv, x, y, text, scale, rgb, max_width, line_gap):
    """Draw wrapped text; returns the y just below the last line."""
    for line in wrap(text, scale, max_width):
        draw_text(cv, x, y, line, scale, rgb)
        y += 7 * scale + line_gap
    return y


# --------------------------------------------------------------------------
# Page layout
# --------------------------------------------------------------------------

def render():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    margin = 36
    inner_w = WIDTH - 2 * margin

    # Masthead
    draw_centered(cv, 26, PAPER_NAME, 4, NAVY)
    draw_centered(cv, 66, DATE_LINE, 5, ACCENT)
    cv.rect(margin, 112, inner_w, 5, RULE)
    cv.rect(margin, 122, inner_w, 2, RULE)

    # Lead story
    y = 140
    draw_text(cv, margin, y, LEAD["kicker"], 2, ACCENT)
    y += 22
    y = draw_block(cv, margin, y, LEAD["headline"], 5, INK, inner_w, 8)
    y += 2
    y = draw_block(cv, margin, y, LEAD["sub"], 2, GREY, inner_w, 5)
    y += 10
    cv.rect(margin, y, inner_w, 3, RULE)
    y += 16

    # Panels: first two side by side, then three across the bottom.
    col_gap = 20
    col_w = (inner_w - col_gap) // 2
    top_y = y
    bottoms = []
    for i, panel in enumerate(PANELS[:2]):
        x = margin + i * (col_w + col_gap)
        bottoms.append(draw_panel(cv, x, top_y, col_w, panel))
    y = max(bottoms) + 14
    cv.rect(margin, y, inner_w, 2, RULE)
    y += 14

    col3_w = (inner_w - 2 * col_gap) // 3
    bottoms = []
    for i, panel in enumerate(PANELS[2:]):
        x = margin + i * (col3_w + col_gap)
        bottoms.append(draw_panel(cv, x, y, col3_w, panel))
    y = max(bottoms) + 14

    # Footer
    cv.rect(margin, HEIGHT - 58, inner_w, 2, RULE)
    draw_centered(cv, HEIGHT - 44, FOOTER, 1, GREY)
    return cv


def draw_panel(cv, x, y, w, panel):
    cv.rect(x, y, w, 4, NAVY)
    y += 12
    draw_text(cv, x, y, panel["kicker"], 2, ACCENT)
    y += 22
    y = draw_block(cv, x, y, panel["headline"], 3, INK, w, 6)
    y += 2
    y = draw_block(cv, x, y, panel["sub"], 2, GREY, w, 5)
    return y


# --------------------------------------------------------------------------
# PNG writer: IHDR, one IDAT of filter-0 scanlines, IEND. zlib output with a
# fixed compression level is byte-for-byte stable across runs.
# --------------------------------------------------------------------------

def chunk(tag, payload):
    out = struct.pack(">I", len(payload)) + tag + payload
    out += struct.pack(">I", binascii.crc32(tag + payload) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(render())
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
