#!/usr/bin/env python3
"""
Build a COLR/CPAL color TrueType font from the 5×9 primitive-grid glyphs (A–Z, a–z, 0–9),
and ALSO generate WOFF + WOFF2 (when possible), writing everything to: ../dist/fonts/

Put this script in: tools/
Outputs:
  dist/fonts/primitives-color.ttf
  dist/fonts/primitives-color.woff
  dist/fonts/primitives-color.woff2   (if brotli/woff2 support is available)

Notes:
- Colors are baked into the font (fonts can't randomize at render-time).
- Each tile gets a deterministic “random” palette color from CRC32 of (glyph, cell, primitive).
"""

from __future__ import annotations

import math
import random
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot


# -----------------------------
# Font / layout config
# -----------------------------
FAMILY_NAME = "Primitives"
STYLE_NAME = "Regular"

UPM = 1000

ASCENT = 700
DESCENT = 300  # positive; written as negative in headers

ADVANCE_WIDTH = 600

GRID_W, GRID_H = 5, 9
CELL = 100
LEFT = 50
TOP = 600

PALETTE_SIZE = 256
PALETTE_SEED = 42

OUT_BASENAME = "primitives-color"

SEAM = 3  # try 1.5–3.0 if needed

# ----------------------------
# Glyph bitmaps (5×9)
# '.' = empty, '#' = filled
# ----------------------------
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
# Primitive selection
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

    if n == 0:
        return 1
    if n == 1:
        if dn:
            return 2
        if up:
            return 3
        if rt:
            return 4
        if lf:
            return 5
        return 0
    if n == 2 and ((up and lf) or (up and rt) or (dn and lf) or (dn and rt)):
        if up and lf:
            return 9
        if up and rt:
            return 6
        if dn and lf:
            return 8
        if dn and rt:
            return 7
        return 0
    return 0


def tiles_for_glyph(g: List[str]) -> List[Tuple[int, int, int]]:
    out: List[Tuple[int, int, int]] = []
    for row in range(GRID_H):
        for col in range(GRID_W):
            pid = pick_primitive(g, col, row)
            if pid is None:
                continue
            out.append((col, row, pid))
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
    ttpen = TTGlyphPen(None)
    pen = Cu2QuPen(ttpen, max_err=1.0, reverse_direction=False)

    s = float(CELL)
    r = s / 2.0
    SEAM = 0.75  # tiny overlap in font units (sub-pixel at typical sizes)

    if pid == 0:
        draw_rect(pen, -SEAM, -SEAM, s, s)

    elif pid == 1:
        pen.moveTo((s, r))
        cubic_arc_to(pen, r, r, r, 0.0, 2.0 * math.pi)
        pen.closePath()

    elif pid == 2:
        pen.moveTo((0, 0))
        pen.lineTo((s, 0))
        cubic_arc_to(pen, r, 0.0, r, 0.0, math.pi)
        pen.closePath()

    elif pid == 3:
        pen.moveTo((0, s))
        pen.lineTo((s, s))
        cubic_arc_to(pen, r, s, r, 0.0, -math.pi)
        pen.closePath()

    elif pid == 4:
        # LEFT half of a circle: flat edge on the RIGHT side of the cell
        pen.moveTo((s, 0))
        pen.lineTo((s, s))
        cubic_arc_to(pen, s, r, r, math.pi / 2.0, 3.0 * math.pi / 2.0)  # left semicircle
        pen.closePath()

    elif pid == 5:
        # RIGHT half of a circle: flat edge on the LEFT side of the cell
        pen.moveTo((0, 0))
        pen.lineTo((0, s))
        cubic_arc_to(pen, 0.0, r, r, math.pi / 2.0, -math.pi / 2.0)      # right semicircle
        pen.closePath()

    elif pid == 6:
        pen.moveTo((0, s))
        pen.lineTo((s, s))
        pen.lineTo((s, 0))
        cubic_arc_to(pen, s, s, s, 3.0 * math.pi / 2.0, math.pi)
        pen.closePath()

    elif pid == 7:
        pen.moveTo((s, s))
        pen.lineTo((s, 0))
        pen.lineTo((0, 0))
        cubic_arc_to(pen, s, 0.0, s, math.pi, math.pi / 2.0)
        pen.closePath()

    elif pid == 8:
        pen.moveTo((s, 0))
        pen.lineTo((0, 0))
        pen.lineTo((0, s))
        cubic_arc_to(pen, 0.0, 0.0, s, math.pi / 2.0, 0.0)
        pen.closePath()

    elif pid == 9:
        pen.moveTo((0, 0))
        pen.lineTo((0, s))
        pen.lineTo((s, s))
        cubic_arc_to(pen, 0.0, s, s, 0.0, -math.pi / 2.0)
        pen.closePath()

    else:
        draw_rect(pen, 0, 0, s, s)

    return ttpen.glyph()


def build_fallback_glyph(bitmap: List[str]):
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
    draw_rect(pen, 100, -200, 500, 600)
    return pen.glyph()


def palette_index_for(glyph_name: str, col: int, row: int, pid: int) -> int:
    b = f"{glyph_name}:{col},{row}:{pid}".encode("utf-8")
    return zlib.crc32(b) % PALETTE_SIZE


# -----------------------------
# Build & repack
# -----------------------------
def build_ttf(out_ttf: Path) -> None:
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    cmap = {ord(ch): codepoint_name(ch) for ch in chars}
    cmap[0x20] = "space"

    base_glyphs = [cmap[ord(ch)] for ch in chars]
    primitives = [f"p{i}" for i in range(10)]
    glyph_order = [".notdef", "space"] + base_glyphs + primitives

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)

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

    glyf = {".notdef": build_notdef(), "space": TTGlyphPen(None).glyph()}
    for i in range(10):
        glyf[f"p{i}"] = build_primitive_glyph(i)
    for ch in chars:
        gname = codepoint_name(ch)
        glyf[gname] = build_fallback_glyph(GLYPHS[ch])

    fb.setupGlyf(glyf)

    # FIX: LSB must match xMin (otherwise some glyphs appear shifted)
    glyf_table = fb.font["glyf"]
    hmtx_table = fb.font["hmtx"]

    for gn in glyph_order:
        g = glyf_table[gn]
        g.recalcBounds(glyf_table)
        x_min = int(getattr(g, "xMin", 0) or 0)

        aw, _ = hmtx_table.metrics.get(gn, (ADVANCE_WIDTH, 0))
        hmtx_table.metrics[gn] = (int(aw), x_min)

    fb.setupMaxp()

    tt = fb.font

    rng = random.Random(PALETTE_SEED)
    palette = [(rng.random(), rng.random(), rng.random(), 1.0) for _ in range(PALETTE_SIZE)]
    tt["CPAL"] = buildCPAL([palette])

    colorGlyphs: Dict[str, dict] = {}
    for ch in chars:
        gname = codepoint_name(ch)
        tiles = tiles_for_glyph(GLYPHS[ch])

        layers: List[dict] = []
        for col, row, pid in tiles:
            dx = LEFT + col * CELL
            dy = TOP - (row + 1) * CELL
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

        colorGlyphs[gname] = {
            "Format": ot.PaintFormat.PaintColrLayers,
            "Layers": layers,
        }

    tt["COLR"] = buildCOLR(colorGlyphs, version=1, glyphMap=tt.getReverseGlyphMap())

    tt.save(out_ttf)


def repack_web_fonts(out_ttf: Path, out_woff: Path, out_woff2: Path) -> None:
    # WOFF
    tt = TTFont(str(out_ttf))
    tt.flavor = "woff"
    tt.save(str(out_woff))

    # WOFF2 (may require brotli; catch and report nicely)
    try:
        tt = TTFont(str(out_ttf))
        tt.flavor = "woff2"
        tt.save(str(out_woff2))
    except Exception as e:
        print(f"NOTE: Could not write WOFF2 ({out_woff2.name}): {e}")
        print("      Install with: pip install brotli")


def copy_stylesheet(root_dir: Path, out_dir: Path) -> None:
    src = root_dir / "src" / "style" / "main.css"
    dst = out_dir / "primitives.css"
    if not src.exists():
        print(f"NOTE: stylesheet not found, skipping: {src}")
        return
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote: {dst}")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    out_dir = root_dir / "dist" / "fonts"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_ttf = out_dir / f"{OUT_BASENAME}.ttf"
    out_woff = out_dir / f"{OUT_BASENAME}.woff"
    out_woff2 = out_dir / f"{OUT_BASENAME}.woff2"

    build_ttf(out_ttf)
    print(f"Wrote: {out_ttf}")

    repack_web_fonts(out_ttf, out_woff, out_woff2)
    print(f"Wrote: {out_woff}")
    if out_woff2.exists():
        print(f"Wrote: {out_woff2}")

    copy_stylesheet(root_dir, out_dir)


if __name__ == "__main__":
    main()
