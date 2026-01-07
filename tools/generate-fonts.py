#!/usr/bin/env python3
"""
Build a COLR/CPAL color TrueType font from the 5×9 primitive-grid glyphs (A–Z, a–z, 0–9)
and write it to: ../dist/fonts/

Put this script in: tools/
Run from repo root or from tools/ (paths are resolved from this file).

Output:
  dist/fonts/primitives-color.ttf

Notes:
- Colors are baked into the font (fonts can't randomize at render-time).
- Each tile (primitive instance) gets a deterministic “random” palette color, derived
  from CRC32 of (glyph, cell, primitive).
"""

from __future__ import annotations

import math
import random
import time
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables import otTables as ot


# -----------------------------
# Font / layout config
# -----------------------------
FAMILY_NAME = "Primitives"
STYLE_NAME = "Color"

UPM = 1000

# Vertical metrics (baseline at y=0; y increases UP)
ASCENT = 700
DESCENT = 300  # (positive number here; will be written as negative where needed)

# Glyph advance (monospace-ish)
ADVANCE_WIDTH = 600

# 5×9 grid, each cell is 100×100 font units
GRID_W, GRID_H = 5, 9
CELL = 100
GRID_PX_W = GRID_W * CELL  # 500
GRID_PX_H = GRID_H * CELL  # 900

# Place grid inside glyph box with margins:
LEFT = 50              # left sidebearing-ish (centers 500 inside 600)
TOP = 600              # top of the 9-row grid (grid runs down to TOP-900 = -300)

# Color palette
PALETTE_SIZE = 256
PALETTE_SEED = 42


# -----------------------------
# Glyph bitmaps (5×9)
# '.' = empty, '#' = filled
# -----------------------------
def bm(s: str) -> List[str]:
    rows = [line.strip() for line in s.strip().splitlines()]
    assert len(rows) == GRID_H
    for r in rows:
        assert len(r) == GRID_W
        assert set(r) <= {".", "#"}
    return rows


GLYPHS: Dict[str, List[str]] = {
    # Uppercase A–Z
    "A": bm("""
        .###.
        #...#
        #...#
        #####
        #...#
        #...#
        #...#
        .....
        .....
    """),
    "B": bm("""
        ####.
        #...#
        #...#
        ####.
        #...#
        #...#
        ####.
        .....
        .....
    """),
    "C": bm("""
        .####
        #....
        #....
        #....
        #....
        #....
        .####
        .....
        .....
    """),
    "D": bm("""
        ####.
        #...#
        #...#
        #...#
        #...#
        #...#
        ####.
        .....
        .....
    """),
    "E": bm("""
        #####
        #....
        #....
        ####.
        #....
        #....
        #####
        .....
        .....
    """),
    "F": bm("""
        #####
        #....
        #....
        ####.
        #....
        #....
        #....
        .....
        .....
    """),
    "G": bm("""
        .####
        #....
        #....
        #.###
        #...#
        #...#
        .###.
        .....
        .....
    """),
    "H": bm("""
        #...#
        #...#
        #...#
        #####
        #...#
        #...#
        #...#
        .....
        .....
    """),
    "I": bm("""
        #####
        ..#..
        ..#..
        ..#..
        ..#..
        ..#..
        #####
        .....
        .....
    """),
    "J": bm("""
        ..###
        ...#.
        ...#.
        ...#.
        ...#.
        #..#.
        .##..
        .....
        .....
    """),
    "K": bm("""
        #...#
        #..#.
        #.#..
        ##...
        #.#..
        #..#.
        #...#
        .....
        .....
    """),
    "L": bm("""
        #....
        #....
        #....
        #....
        #....
        #....
        #####
        .....
        .....
    """),
    "M": bm("""
        #...#
        ##.##
        #.#.#
        #...#
        #...#
        #...#
        #...#
        .....
        .....
    """),
    "N": bm("""
        #...#
        ##..#
        #.#.#
        #..##
        #...#
        #...#
        #...#
        .....
        .....
    """),
    "O": bm("""
        .###.
        #...#
        #...#
        #...#
        #...#
        #...#
        .###.
        .....
        .....
    """),
    "P": bm("""
        ####.
        #...#
        #...#
        ####.
        #....
        #....
        #....
        .....
        .....
    """),
    "Q": bm("""
        .###.
        #...#
        #...#
        #...#
        #.#.#
        #..#.
        .##.#
        .....
        .....
    """),
    "R": bm("""
        ####.
        #...#
        #...#
        ####.
        #.#..
        #..#.
        #...#
        .....
        .....
    """),
    "S": bm("""
        .####
        #....
        #....
        .###.
        ....#
        ....#
        ####.
        .....
        .....
    """),
    "T": bm("""
        #####
        ..#..
        ..#..
        ..#..
        ..#..
        ..#..
        ..#..
        .....
        .....
    """),
    "U": bm("""
        #...#
        #...#
        #...#
        #...#
        #...#
        #...#
        .###.
        .....
        .....
    """),
    "V": bm("""
        #...#
        #...#
        #...#
        #...#
        #...#
        .#.#.
        ..#..
        .....
        .....
    """),
    "W": bm("""
        #...#
        #...#
        #...#
        #...#
        #.#.#
        ##.##
        #...#
        .....
        .....
    """),
    "X": bm("""
        #...#
        #...#
        .#.#.
        ..#..
        .#.#.
        #...#
        #...#
        .....
        .....
    """),
    "Y": bm("""
        #...#
        #...#
        .#.#.
        ..#..
        ..#..
        ..#..
        ..#..
        .....
        .....
    """),
    "Z": bm("""
        #####
        ....#
        ...#.
        ..#..
        .#...
        #....
        #####
        .....
        .....
    """),

    # Lowercase a–z
    "a": bm("""
        .....
        .....
        .###.
        ....#
        .####
        #...#
        .####
        .....
        .....
    """),
    "b": bm("""
        #....
        #....
        ####.
        #...#
        #...#
        #...#
        ####.
        .....
        .....
    """),
    "c": bm("""
        .....
        .....
        .####
        #....
        #....
        #....
        .####
        .....
        .....
    """),
    "d": bm("""
        ....#
        ....#
        .####
        #...#
        #...#
        #...#
        .####
        .....
        .....
    """),
    "e": bm("""
        .....
        .....
        .###.
        #...#
        #####
        #....
        .####
        .....
        .....
    """),
    "f": bm("""
        ..##.
        .#..#
        .#...
        ###..
        .#...
        .#...
        .#...
        .....
        .....
    """),
    "g": bm("""
        .....
        .....
        .####
        #...#
        #...#
        .####
        ....#
        .###.
        .....
    """),
    "h": bm("""
        #....
        #....
        ####.
        #...#
        #...#
        #...#
        #...#
        .....
        .....
    """),
    "i": bm("""
        ..#..
        .....
        .##..
        ..#..
        ..#..
        ..#..
        .###.
        .....
        .....
    """),
    "j": bm("""
        ...#.
        .....
        ..##.
        ...#.
        ...#.
        ...#.
        #..#.
        .##..
        .....
    """),
    "k": bm("""
        #....
        #....
        #..#.
        #.#..
        ##...
        #.#..
        #..#.
        .....
        .....
    """),
    "l": bm("""
        .##..
        ..#..
        ..#..
        ..#..
        ..#..
        ..#..
        .###.
        .....
        .....
    """),
    "m": bm("""
        .....
        .....
        ##.#.
        #.#.#
        #.#.#
        #...#
        #...#
        .....
        .....
    """),
    "n": bm("""
        .....
        .....
        ####.
        #...#
        #...#
        #...#
        #...#
        .....
        .....
    """),
    "o": bm("""
        .....
        .....
        .###.
        #...#
        #...#
        #...#
        .###.
        .....
        .....
    """),
    "p": bm("""
        .....
        .....
        ####.
        #...#
        #...#
        ####.
        #....
        #....
        .....
    """),
    "q": bm("""
        .....
        .....
        .####
        #...#
        #...#
        .####
        ....#
        ....#
        .....
    """),
    "r": bm("""
        .....
        .....
        ####.
        #...#
        #....
        #....
        #....
        .....
        .....
    """),
    "s": bm("""
        .....
        .....
        .####
        #....
        .###.
        ....#
        ####.
        .....
        .....
    """),
    "t": bm("""
        ..#..
        ..#..
        ####.
        ..#..
        ..#..
        ..#..
        ...##
        .....
        .....
    """),
    "u": bm("""
        .....
        .....
        #...#
        #...#
        #...#
        #...#
        .####
        .....
        .....
    """),
    "v": bm("""
        .....
        .....
        #...#
        #...#
        #...#
        .#.#.
        ..#..
        .....
        .....
    """),
    "w": bm("""
        .....
        .....
        #...#
        #...#
        #.#.#
        #.#.#
        .#.#.
        .....
        .....
    """),
    "x": bm("""
        .....
        .....
        #...#
        .#.#.
        ..#..
        .#.#.
        #...#
        .....
        .....
    """),
    "y": bm("""
        .....
        .....
        #...#
        #...#
        #...#
        .####
        ....#
        .###.
        .....
    """),
    "z": bm("""
        .....
        .....
        #####
        ...#.
        ..#..
        .#...
        #####
        .....
        .....
    """),

    # Digits 0–9
    "0": bm("""
        .###.
        #...#
        #..##
        #.#.#
        ##..#
        #...#
        .###.
        .....
        .....
    """),
    "1": bm("""
        ..#..
        .##..
        ..#..
        ..#..
        ..#..
        ..#..
        .###.
        .....
        .....
    """),
    "2": bm("""
        .###.
        #...#
        ....#
        ...#.
        ..#..
        .#...
        #####
        .....
        .....
    """),
    "3": bm("""
        ####.
        ....#
        ...#.
        ..##.
        ....#
        #...#
        .###.
        .....
        .....
    """),
    "4": bm("""
        ...#.
        ..##.
        .#.#.
        #..#.
        #####
        ...#.
        ...#.
        .....
        .....
    """),
    "5": bm("""
        #####
        #....
        ####.
        ....#
        ....#
        #...#
        .###.
        .....
        .....
    """),
    "6": bm("""
        .###.
        #....
        ####.
        #...#
        #...#
        #...#
        .###.
        .....
        .....
    """),
    "7": bm("""
        #####
        ....#
        ...#.
        ..#..
        .#...
        .#...
        .#...
        .....
        .....
    """),
    "8": bm("""
        .###.
        #...#
        #...#
        .###.
        #...#
        #...#
        .###.
        .....
        .....
    """),
    "9": bm("""
        .###.
        #...#
        #...#
        .####
        ....#
        ...#.
        .##..
        .....
        .....
    """),
}


# -----------------------------
# Bitmap -> primitive selection
# -----------------------------
def is_on(g: List[str], x: int, y: int) -> bool:
    return 0 <= x < GRID_W and 0 <= y < GRID_H and g[y][x] == "#"


def pick_primitive(g: List[str], x: int, y: int) -> Optional[int]:
    if not is_on(g, x, y):
        return None

    up = is_on(g, x, y - 1)
    dn = is_on(g, x, y + 1)
    lf = is_on(g, x - 1, y)
    rt = is_on(g, x + 1, y)
    n = int(up) + int(dn) + int(lf) + int(rt)

    # isolated
    if n == 0:
        return 1

    # endpoints -> half circles
    if n == 1:
        if dn:
            return 2  # flat bottom
        if up:
            return 3  # flat top
        if rt:
            return 5  # flat right
        if lf:
            return 4  # flat left
        return 0

    # corners -> diagonal wedges
    if n == 2 and ((up and lf) or (up and rt) or (dn and lf) or (dn and rt)):
        if up and lf:
            return 9  # top-left wedge
        if up and rt:
            return 6  # top-right wedge
        if dn and lf:
            return 8  # bottom-left wedge
        if dn and rt:
            return 7  # bottom-right wedge
        return 0

    # straights / junctions
    return 0


def tiles_for_glyph(g: List[str]) -> List[Tuple[int, int, int, int]]:
    """
    Returns list of (col, row, pid, paletteIndexHint)
    """
    out: List[Tuple[int, int, int, int]] = []
    for row in range(GRID_H):
        for col in range(GRID_W):
            pid = pick_primitive(g, col, row)
            if pid is None:
                continue
            out.append((col, row, pid, 0))
    return out


def codepoint_name(ch: str) -> str:
    cp = ord(ch)
    return f"U{cp:04X}" if cp <= 0xFFFF else f"U{cp:06X}"


# -----------------------------
# Primitive outlines (glyf)
# -----------------------------
def draw_rect(pen: TTGlyphPen, x0: float, y0: float, x1: float, y1: float) -> None:
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()


def cubic_arc_to(pen, cx: float, cy: float, r: float, a0: float, a1: float) -> None:
    """
    Add cubic Bezier arc(s) from a0 to a1 around center (cx,cy), radius r.
    Works for CW or CCW depending on sign of (a1-a0).
    """
    da = a1 - a0
    if da == 0:
        return
    nseg = max(1, int(math.ceil(abs(da) / (math.pi / 2))))
    step = da / nseg

    for i in range(nseg):
        t0 = a0 + i * step
        t1 = t0 + step

        x0 = cx + r * math.cos(t0)
        y0 = cy + r * math.sin(t0)
        x3 = cx + r * math.cos(t1)
        y3 = cy + r * math.sin(t1)

        k = 4.0 / 3.0 * math.tan((t1 - t0) / 4.0)

        dx0 = -r * math.sin(t0)
        dy0 = r * math.cos(t0)
        dx1 = -r * math.sin(t1)
        dy1 = r * math.cos(t1)

        x1 = x0 + k * dx0
        y1 = y0 + k * dy0
        x2 = x3 - k * dx1
        y2 = y3 - k * dy1

        pen.curveTo((x1, y1), (x2, y2), (x3, y3))


def build_primitive_glyph(pid: int):
    """
    Build one of the 10 primitive glyphs in a CELL×CELL box, origin at (0,0).
    """
    ttpen = TTGlyphPen(None)
    pen = Cu2QuPen(ttpen, max_err=1.0, reverse_direction=False)

    s = float(CELL)
    r = s / 2.0

    if pid == 0:
        draw_rect(pen, 0, 0, s, s)

    elif pid == 1:
        # full circle
        pen.moveTo((s, r))
        cubic_arc_to(pen, r, r, r, 0.0, 2.0 * math.pi)
        pen.closePath()

    elif pid == 2:
        # semicircle bulge UP, flat bottom on y=0
        pen.moveTo((0, 0))
        pen.lineTo((s, 0))
        # start at angle 0 at (s,0) around center (r,0)
        cubic_arc_to(pen, r, 0.0, r, 0.0, math.pi)
        pen.closePath()

    elif pid == 3:
        # semicircle bulge DOWN, flat top on y=s
        pen.moveTo((0, s))
        pen.lineTo((s, s))
        # start at angle 0 at (s,s) around center (r,s), go CW to -pi
        cubic_arc_to(pen, r, s, r, 0.0, -math.pi)
        pen.closePath()

    elif pid == 4:
        # semicircle bulge RIGHT, flat left on x=0
        pen.moveTo((0, 0))
        pen.lineTo((0, s))
        # from top (pi/2) to bottom (-pi/2) around center (0,r), CW
        cubic_arc_to(pen, 0.0, r, r, math.pi / 2.0, -math.pi / 2.0)
        pen.closePath()

    elif pid == 5:
        # semicircle bulge LEFT, flat right on x=s
        pen.moveTo((s, 0))
        pen.lineTo((s, s))
        # from top (pi/2) to bottom (3pi/2) around center (s,r), CCW
        cubic_arc_to(pen, s, r, r, math.pi / 2.0, 3.0 * math.pi / 2.0)
        pen.closePath()

    elif pid == 6:
        # top-right wedge (big quarter circle, radius s, center at (s,s))
        pen.moveTo((0, s))
        pen.lineTo((s, s))
        pen.lineTo((s, 0))
        cubic_arc_to(pen, s, s, s, 3.0 * math.pi / 2.0, math.pi)  # CW 90°
        pen.closePath()

    elif pid == 7:
        # bottom-right wedge (center at (s,0))
        pen.moveTo((s, s))
        pen.lineTo((s, 0))
        pen.lineTo((0, 0))
        cubic_arc_to(pen, s, 0.0, s, math.pi, math.pi / 2.0)  # CW 90°
        pen.closePath()

    elif pid == 8:
        # bottom-left wedge (center at (0,0))
        pen.moveTo((s, 0))
        pen.lineTo((0, 0))
        pen.lineTo((0, s))
        cubic_arc_to(pen, 0.0, 0.0, s, math.pi / 2.0, 0.0)  # CW 90°
        pen.closePath()

    elif pid == 9:
        # top-left wedge (center at (0,s))
        pen.moveTo((0, 0))
        pen.lineTo((0, s))
        pen.lineTo((s, s))
        cubic_arc_to(pen, 0.0, s, s, 0.0, -math.pi / 2.0)  # CW 90°
        pen.closePath()

    else:
        draw_rect(pen, 0, 0, s, s)

    return ttpen.glyph()


# -----------------------------
# Fallback (monochrome) glyphs
# -----------------------------
def build_fallback_glyph(bitmap: List[str]):
    """
    Fallback outline: union of filled cell rectangles.
    """
    pen = TTGlyphPen(None)
    for row in range(GRID_H):
        for col in range(GRID_W):
            if bitmap[row][col] != "#":
                continue
            x0 = LEFT + col * CELL
            y1 = TOP - row * CELL
            y0 = y1 - CELL
            draw_rect(pen, x0, y0, x0 + CELL, y1)
    return pen.glyph()


def build_notdef():
    pen = TTGlyphPen(None)
    draw_rect(pen, 50, -250, 550, 650)
    # inner counter
    draw_rect(pen, 100, -200, 500, 600)
    return pen.glyph()


def palette_index_for(glyph_name: str, col: int, row: int, pid: int) -> int:
    b = f"{glyph_name}:{col},{row}:{pid}".encode("utf-8")
    return zlib.crc32(b) % PALETTE_SIZE


# -----------------------------
# Main build
# -----------------------------
def main() -> None:
    script_dir = Path(__file__).resolve().parent          # tools/
    root_dir = script_dir.parent                          # project root
    out_dir = root_dir / "dist" / "fonts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Characters included
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    cmap = {ord(ch): codepoint_name(ch) for ch in chars}
    cmap[0x20] = "space"

    # Glyph order
    base_glyphs = [cmap[ord(ch)] for ch in chars]
    primitives = [f"p{i}" for i in range(10)]
    glyph_order = [".notdef", "space"] + base_glyphs + primitives

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)

    # Metrics
    hmtx = {g: (ADVANCE_WIDTH, 0) for g in glyph_order}
    hmtx["space"] = (ADVANCE_WIDTH, 0)
    for p in primitives:
        hmtx[p] = (CELL, 0)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=-DESCENT)
    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=-DESCENT,
        usWinAscent=ASCENT,
        usWinDescent=DESCENT,
    )
    fb.setupNameTable(
        {
            "familyName": FAMILY_NAME,
            "styleName": STYLE_NAME,
            "fullName": f"{FAMILY_NAME} {STYLE_NAME}",
            "uniqueFontIdentifier": f"{FAMILY_NAME}-{STYLE_NAME}",
            "psName": f"{FAMILY_NAME}-{STYLE_NAME}".replace(" ", ""),
        }
    )
    fb.setupPost()

    # Build glyf outlines
    glyf = {".notdef": build_notdef(), "space": TTGlyphPen(None).glyph()}
    for i in range(10):
        glyf[f"p{i}"] = build_primitive_glyph(i)

    # Fallback glyphs for characters
    for ch in chars:
        gname = codepoint_name(ch)
        glyf[gname] = build_fallback_glyph(GLYPHS[ch])

    fb.setupGlyf(glyf)
    fb.setupMaxp()

    tt = fb.font

    # CPAL palette (single palette)
    rng = random.Random(PALETTE_SEED)
    palette = [(rng.random(), rng.random(), rng.random(), 1.0) for _ in range(PALETTE_SIZE)]
    tt["CPAL"] = buildCPAL([palette])

    # COLR v1 paint graphs
    colorGlyphs: Dict[str, dict] = {}

    for ch in chars:
        gname = codepoint_name(ch)
        tiles = tiles_for_glyph(GLYPHS[ch])

        layers: List[dict] = []
        for col, row, pid, _ in tiles:
            # placement
            dx = LEFT + col * CELL
            dy = TOP - (row + 1) * CELL  # bottom of the cell

            pidx = palette_index_for(gname, col, row, pid)

            layers.append(
                {
                    "Format": ot.PaintFormat.PaintTransform,
                    "Paint": {
                        "Format": ot.PaintFormat.PaintGlyph,
                        "Glyph": f"p{pid}",
                        "Paint": {
                            "Format": ot.PaintFormat.PaintSolid,
                            "PaletteIndex": pidx,
                            "Alpha": 1.0,
                        },
                    },
                    "Transform": {
                        "xx": 1.0,
                        "yx": 0.0,
                        "xy": 0.0,
                        "yy": 1.0,
                        "dx": dx,
                        "dy": dy,
                    },
                }
            )

        # Wrap layers in PaintColrLayers (important!)
        colorGlyphs[gname] = {
            "Format": ot.PaintFormat.PaintColrLayers,
            "Layers": layers,
        }

    tt["COLR"] = buildCOLR(colorGlyphs, version=1, glyphMap=tt.getReverseGlyphMap())

    out_path = out_dir / "primitives-color.ttf"
    tt.save(out_path)

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
