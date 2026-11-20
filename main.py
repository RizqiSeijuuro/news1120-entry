#!/usr/bin/env python3
"""
entry.py / main.py -- make.fun bounty "news-image-20261120"

Renders a single 1024x1024 PNG ("entry.png") summarizing six real-world
news stories from 20 November 2026:

  1. Trump, Xi Jinping and Putin hold an unprecedented first-ever
     trilateral summit in Shenzhen, China, pledging nuclear war must
     never be fought.
  2. The ICJ rules Myanmar committed genocide against the Rohingya --
     the first time the court has held a state responsible for genocide.
  3. Yemen's Houthis claim attacks on a Saudi airport and financial
     facilities in Riyadh amid escalating cross-border strikes.
  4. Somalia orders the UAE's ambassador to leave within 72 hours and
     recalls its own envoy, amid a diplomatic standoff.
  5. The US NSA's internal classified communication systems are
     partially down for a third straight day.
  6. GTA VI receives widespread critical acclaim following its global
     release.

Everything here is standard-library only (zlib + struct for a hand-rolled
PNG encoder, no third-party imaging libraries, no network access). The
image layout, colors and text are fully deterministic -- running the
script twice produces byte-identical output.
"""

import os
import struct
import zlib

# --------------------------------------------------------------------------
# Canvas / palette
# --------------------------------------------------------------------------

WIDTH = 1024
HEIGHT = 1024

NAVY = (11, 17, 36)
NAVY_LIGHT = (21, 30, 56)
NAVY_ACCENT = (30, 41, 74)
WHITE = (241, 245, 250)
GRAY = (168, 180, 202)
DIM_GRAY = (120, 132, 156)
GOLD = (236, 186, 74)
GOLD_DARK = (190, 142, 46)
BLUE = (86, 154, 240)
RED = (233, 86, 78)
ORANGE = (240, 142, 62)
ORANGE_DARK = (92, 62, 22)
CYAN = (72, 212, 212)
GREEN = (108, 210, 128)
DARK_GREEN = (22, 34, 24)

pixels = bytearray(NAVY * (WIDTH * HEIGHT))


def set_pixel(x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        i = (y * WIDTH + x) * 3
        pixels[i] = color[0]
        pixels[i + 1] = color[1]
        pixels[i + 2] = color[2]


def fill_rect(x, y, w, h, color):
    if w <= 0 or h <= 0:
        return
    x0 = max(x, 0)
    x1 = min(x + w, WIDTH)
    y0 = max(y, 0)
    y1 = min(y + h, HEIGHT)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        i0 = (yy * WIDTH + x0) * 3
        i1 = i0 + len(row)
        pixels[i0:i1] = row


def fill_circle(cx, cy, r, color):
    r2 = r * r
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        rem = r2 - dy * dy
        if rem < 0:
            continue
        dx = int(rem ** 0.5)
        fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)


def fill_triangle(p1, p2, p3, color):
    xs = (p1[0], p2[0], p3[0])
    ys = (p1[1], p2[1], p3[1])
    minx, maxx = max(min(xs), 0), min(max(xs), WIDTH - 1)
    miny, maxy = max(min(ys), 0), min(max(ys), HEIGHT - 1)
    (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
    denom = (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3)
    if denom == 0:
        return
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            a = ((x2 - xx) * (y3 - yy) - (x3 - xx) * (y2 - yy)) / denom
            b = ((x3 - xx) * (y1 - yy) - (x1 - xx) * (y3 - yy)) / denom
            c = 1 - a - b
            if a >= 0 and b >= 0 and c >= 0:
                set_pixel(xx, yy, color)


def draw_line(x0, y0, x1, y1, color, thickness=3):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        t = i / steps
        x = round(x0 + (x1 - x0) * t)
        y = round(y0 + (y1 - y0) * t)
        fill_rect(x - thickness // 2, y - thickness // 2, thickness, thickness, color)


# --------------------------------------------------------------------------
# Hand-rolled 5x7 bitmap font: A-Z, 0-9, space, . , ' - : $ % /
# --------------------------------------------------------------------------

def _g(rows):
    return [[1 if c == "1" else 0 for c in row] for row in rows]


FONT = {
    " ": _g(["00000"] * 7),
    "A": _g(["00100", "01010", "10001", "11111", "10001", "10001", "10001"]),
    "B": _g(["11110", "10001", "10001", "11110", "10001", "10001", "11110"]),
    "C": _g(["01111", "10000", "10000", "10000", "10000", "10000", "01111"]),
    "D": _g(["11110", "10001", "10001", "10001", "10001", "10001", "11110"]),
    "E": _g(["11111", "10000", "10000", "11110", "10000", "10000", "11111"]),
    "F": _g(["11111", "10000", "10000", "11110", "10000", "10000", "10000"]),
    "G": _g(["01111", "10000", "10000", "10111", "10001", "10001", "01111"]),
    "H": _g(["10001", "10001", "10001", "11111", "10001", "10001", "10001"]),
    "I": _g(["11111", "00100", "00100", "00100", "00100", "00100", "11111"]),
    "J": _g(["00111", "00010", "00010", "00010", "00010", "10010", "01100"]),
    "K": _g(["10001", "10010", "10100", "11000", "10100", "10010", "10001"]),
    "L": _g(["10000", "10000", "10000", "10000", "10000", "10000", "11111"]),
    "M": _g(["10001", "11011", "10101", "10101", "10001", "10001", "10001"]),
    "N": _g(["10001", "11001", "10101", "10011", "10001", "10001", "10001"]),
    "O": _g(["01110", "10001", "10001", "10001", "10001", "10001", "01110"]),
    "P": _g(["11110", "10001", "10001", "11110", "10000", "10000", "10000"]),
    "Q": _g(["01110", "10001", "10001", "10001", "10101", "10010", "01101"]),
    "R": _g(["11110", "10001", "10001", "11110", "10100", "10010", "10001"]),
    "S": _g(["01111", "10000", "10000", "01110", "00001", "00001", "11110"]),
    "T": _g(["11111", "00100", "00100", "00100", "00100", "00100", "00100"]),
    "U": _g(["10001", "10001", "10001", "10001", "10001", "10001", "01110"]),
    "V": _g(["10001", "10001", "10001", "10001", "01010", "01010", "00100"]),
    "W": _g(["10001", "10001", "10001", "10101", "10101", "11011", "10001"]),
    "X": _g(["10001", "01010", "00100", "00100", "00100", "01010", "10001"]),
    "Y": _g(["10001", "01010", "00100", "00100", "00100", "00100", "00100"]),
    "Z": _g(["11111", "00001", "00010", "00100", "01000", "10000", "11111"]),
    "0": _g(["01110", "10001", "10011", "10101", "11001", "10001", "01110"]),
    "1": _g(["00100", "01100", "00100", "00100", "00100", "00100", "01110"]),
    "2": _g(["01110", "10001", "00001", "00110", "01000", "10000", "11111"]),
    "3": _g(["01110", "10001", "00001", "00110", "00001", "10001", "01110"]),
    "4": _g(["10001", "10001", "10001", "11111", "00001", "00001", "00001"]),
    "5": _g(["11111", "10000", "10000", "11110", "00001", "10001", "01110"]),
    "6": _g(["01110", "10000", "10000", "11110", "10001", "10001", "01110"]),
    "7": _g(["11111", "00001", "00010", "00100", "01000", "01000", "01000"]),
    "8": _g(["01110", "10001", "10001", "01110", "10001", "10001", "01110"]),
    "9": _g(["01110", "10001", "10001", "01111", "00001", "00001", "01110"]),
    ".": _g(["00000", "00000", "00000", "00000", "00000", "00000", "00100"]),
    ",": _g(["00000", "00000", "00000", "00000", "00000", "00100", "01000"]),
    "'": _g(["00100", "00100", "00000", "00000", "00000", "00000", "00000"]),
    "-": _g(["00000", "00000", "00000", "11111", "00000", "00000", "00000"]),
    ":": _g(["00000", "00100", "00000", "00000", "00000", "00100", "00000"]),
    "$": _g(["00100", "01111", "10000", "01110", "00001", "11110", "00100"]),
    "%": _g(["10001", "00001", "00010", "00100", "01000", "10000", "10001"]),
    "/": _g(["00001", "00010", "00010", "00100", "01000", "01000", "10000"]),
}

GLYPH_COLS = 5
GLYPH_ROWS = 7
CHAR_ADVANCE = GLYPH_COLS + 1  # 1px spacing column after each glyph


def draw_char(x, y, ch, scale, color):
    glyph = FONT.get(ch.upper())
    if glyph is None:
        return
    for row in range(GLYPH_ROWS):
        for col in range(GLYPH_COLS):
            if glyph[row][col]:
                fill_rect(x + col * scale, y + row * scale, scale, scale, color)


def draw_text(x, y, text, scale, color):
    cx = x
    for ch in text:
        draw_char(cx, y, ch, scale, color)
        cx += CHAR_ADVANCE * scale
    return cx


def text_width(text, scale):
    """Pixel width of `text` at `scale` (no trailing inter-char gap)."""
    if not text:
        return 0
    return len(text) * CHAR_ADVANCE * scale - scale


def max_chars_for_width(width_px, scale):
    """How many characters of this font/scale fit within width_px."""
    return (width_px + scale) // (CHAR_ADVANCE * scale)


def draw_text_centered(cx, y, text, scale, color):
    w = text_width(text, scale)
    draw_text(cx - w // 2, y, text, scale, color)


# --------------------------------------------------------------------------
# Story icons -- small geometric glyphs drawn with rects/circles/triangles
# --------------------------------------------------------------------------

def icon_summit(cx, cy):
    """Three overlapping circles: three leaders at one table."""
    fill_circle(cx - 17, cy + 9, 20, GOLD_DARK)
    fill_circle(cx + 17, cy + 9, 20, GOLD_DARK)
    fill_circle(cx, cy - 14, 20, GOLD)


def icon_scales(cx, cy):
    """Balance scale: international law / court ruling."""
    fill_rect(cx - 2, cy - 24, 4, 44, BLUE)
    fill_rect(cx - 26, cy - 24, 52, 5, BLUE)
    fill_circle(cx - 26, cy - 8, 9, BLUE)
    fill_circle(cx + 26, cy - 8, 9, BLUE)
    fill_rect(cx - 16, cy + 20, 32, 6, BLUE)


def icon_strike(cx, cy):
    """Missile / strike glyph: Middle East conflict."""
    fill_triangle((cx, cy - 26), (cx - 20, cy + 14), (cx + 20, cy + 14), RED)
    fill_rect(cx - 6, cy + 14, 12, 12, ORANGE)


def icon_standoff(cx, cy):
    """Two arrows pulling apart: diplomatic standoff."""
    fill_triangle((cx - 30, cy), (cx - 10, cy - 11), (cx - 10, cy + 11), ORANGE)
    fill_triangle((cx + 30, cy), (cx + 10, cy - 11), (cx + 10, cy + 11), ORANGE)
    fill_rect(cx - 4, cy - 3, 8, 6, ORANGE_DARK)


def icon_breach(cx, cy):
    """Shield with a crack: security systems disrupted."""
    fill_triangle((cx - 22, cy - 18), (cx + 22, cy - 18), (cx, cy + 26), CYAN)
    fill_rect(cx - 22, cy - 22, 44, 10, CYAN)
    draw_line(cx - 13, cy - 6, cx + 13, cy + 16, NAVY, 5)
    draw_line(cx + 13, cy - 6, cx - 13, cy + 16, NAVY, 5)


def icon_game(cx, cy):
    """Game controller: pop-culture / GTA VI release."""
    fill_rect(cx - 28, cy - 10, 56, 22, GREEN)
    fill_circle(cx - 18, cy + 1, 12, GREEN)
    fill_circle(cx + 18, cy + 1, 12, GREEN)
    fill_circle(cx - 12, cy + 1, 5, DARK_GREEN)
    fill_circle(cx + 12, cy - 4, 5, DARK_GREEN)
    fill_circle(cx + 18, cy + 5, 5, DARK_GREEN)
    fill_rect(cx - 23, cy - 3, 8, 2, DARK_GREEN)
    fill_rect(cx - 20, cy - 6, 2, 8, DARK_GREEN)


# --------------------------------------------------------------------------
# Story content -- title + up to 3 short caption lines per card
# --------------------------------------------------------------------------

CARDS = [
    {
        "color": GOLD,
        "icon": icon_summit,
        "lines": [
            "FIRST TRUMP-XI-PUTIN SUMMIT",
            "HELD IN SHENZHEN, CHINA",
            "PLEDGE: NO NUCLEAR WAR EVER",
        ],
    },
    {
        "color": BLUE,
        "icon": icon_scales,
        "lines": [
            "ICJ RULES MYANMAR COMMITTED",
            "GENOCIDE AGAINST ROHINGYA",
            "FIRST STATE HELD LIABLE",
        ],
    },
    {
        "color": RED,
        "icon": icon_strike,
        "lines": [
            "HOUTHIS CLAIM STRIKES ON",
            "RIYADH AIRPORT AND BANKS",
            "SAUDI-YEMEN CLASHES ESCALATE",
        ],
    },
    {
        "color": ORANGE,
        "icon": icon_standoff,
        "lines": [
            "SOMALIA EXPELS UAE ENVOY",
            "72 HOUR DEADLINE TO LEAVE",
            "BOTH NATIONS RECALL ENVOYS",
        ],
    },
    {
        "color": CYAN,
        "icon": icon_breach,
        "lines": [
            "US NSA SYSTEMS DISRUPTED",
            "CLASSIFIED NETWORKS DOWN",
            "THIRD STRAIGHT DAY OF ISSUES",
        ],
    },
    {
        "color": GREEN,
        "icon": icon_game,
        "lines": [
            "GTA VI LAUNCHES WORLDWIDE",
            "CRITICS HAIL IT AS A",
            "LANDMARK GAMING ACHIEVEMENT",
        ],
    },
]

TITLE_TEXT = "WORLD NEWS"
DATE_TEXT = "NOVEMBER 20, 2026"
FOOTER_TEXT = "WORLD NEWS SUMMARY - MAKE.FUN ENTRY"

# --------------------------------------------------------------------------
# Layout constants
# --------------------------------------------------------------------------

TITLE_BAR_H = 96
OUTER_MARGIN = 28
GRID_GAP = 20
CARD_PAD = 18
ICON_BOX = 64
ICON_GAP = 16
CAPTION_SCALE = 2
LINE_GAP = 6

GRID_TOP = TITLE_BAR_H + 20
GRID_BOTTOM = HEIGHT - OUTER_MARGIN - 34  # leave room for footer
GRID_WIDTH = WIDTH - 2 * OUTER_MARGIN
GRID_HEIGHT = GRID_BOTTOM - GRID_TOP

CARD_W = (GRID_WIDTH - GRID_GAP) // 2
CARD_H = (GRID_HEIGHT - 2 * GRID_GAP) // 3

CONTENT_W = CARD_W - 2 * CARD_PAD
CONTENT_H = CARD_H - 2 * CARD_PAD

LINE_HEIGHT = GLYPH_ROWS * CAPTION_SCALE + LINE_GAP
MAX_CHARS = max_chars_for_width(CONTENT_W, CAPTION_SCALE)

# Validate every caption line fits the computed card text width BEFORE
# any drawing happens -- fail loudly instead of silently clipping text.
for _card in CARDS:
    for _line in _card["lines"]:
        assert len(_line) <= MAX_CHARS, (
            f"caption line too long for card width: {_line!r} "
            f"({len(_line)} chars > {MAX_CHARS} max)"
        )
        for _ch in _line:
            assert _ch.upper() in FONT, f"character not in font: {_ch!r}"


# --------------------------------------------------------------------------
# Compose the image
# --------------------------------------------------------------------------

def draw_title_bar():
    fill_rect(0, 0, WIDTH, TITLE_BAR_H, NAVY_LIGHT)
    fill_rect(0, TITLE_BAR_H - 4, WIDTH, 4, GOLD)
    draw_text_centered(WIDTH // 2, 20, TITLE_TEXT, 6, WHITE)
    draw_text_centered(WIDTH // 2, 70, DATE_TEXT, 2, GRAY)


def draw_footer():
    y = HEIGHT - OUTER_MARGIN - 20
    fill_rect(OUTER_MARGIN, y - 10, GRID_WIDTH, 2, NAVY_ACCENT)
    draw_text_centered(WIDTH // 2, y, FOOTER_TEXT, 1, DIM_GRAY)


def draw_card(card, x, y):
    fill_rect(x, y, CARD_W, CARD_H, NAVY_LIGHT)
    fill_rect(x, y, CARD_W, 6, card["color"])

    content_x = x + CARD_PAD
    content_y = y + 6 + CARD_PAD

    icon_cx = content_x + ICON_BOX // 2
    icon_cy = content_y + ICON_BOX // 2
    card["icon"](icon_cx, icon_cy)

    text_y = content_y + ICON_BOX + ICON_GAP
    text_colors = [WHITE, GRAY, GRAY]
    for i, line in enumerate(card["lines"]):
        draw_text(content_x, text_y, line, CAPTION_SCALE, text_colors[i % len(text_colors)])
        text_y += LINE_HEIGHT


def draw_grid():
    for idx, card in enumerate(CARDS):
        row = idx // 2
        col = idx % 2
        x = OUTER_MARGIN + col * (CARD_W + GRID_GAP)
        y = GRID_TOP + row * (CARD_H + GRID_GAP)
        draw_card(card, x, y)


def render():
    draw_title_bar()
    draw_grid()
    draw_footer()


# --------------------------------------------------------------------------
# Minimal PNG encoder (stdlib only: struct + zlib)
# --------------------------------------------------------------------------

def _chunk(tag, data):
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_png(path, width, height, rgb):
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    stride = width * 3
    raw = bytearray()
    for row in range(height):
        raw.append(0)  # filter type 0 (None) for every scanline
        raw.extend(rgb[row * stride:(row + 1) * stride])

    idat = zlib.compress(bytes(raw), 9)

    with open(path, "wb") as f:
        f.write(sig)
        f.write(_chunk(b"IHDR", ihdr))
        f.write(_chunk(b"IDAT", idat))
        f.write(_chunk(b"IEND", b""))


def main():
    # Deterministic render: no RNG, no network, no wall-clock-dependent
    # content, so re-running this always produces byte-identical PNG bytes.
    render()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    write_png(out_path, WIDTH, HEIGHT, pixels)
    print(f"wrote {out_path} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
