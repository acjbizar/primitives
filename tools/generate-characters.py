#!/usr/bin/env python3
"""
Generate 5×9 glyph SVGs for A–Z, a–z, 0–9 using ONLY the 10 primitives,
but with a RANDOM RGB fill PER TILE (per primitive instance).

- Script location: tools/
- Output: ../sketches/alphabet-5x9-manual-rgb/
  - upper-A.svg ... upper-Z.svg
  - lower-a.svg ... lower-z.svg
  - digit-0.svg  ... digit-9.svg
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional

GRID_W, GRID_H = 5, 9
D = 48  # tile size (each primitive uses viewBox 48×48)


# ----------------------------
# Glyph bitmaps (5×9)
# '.' = empty, '#' = filled
# ----------------------------
def bm(s: str) -> List[str]:
    rows = [line.strip() for line in s.strip().splitlines()]
    assert len(rows) == GRID_H, f"Expected {GRID_H} rows, got {len(rows)}"
    for r in rows:
        assert len(r) == GRID_W, f"Expected {GRID_W} cols, got {len(r)} in row: {r!r}"
        for ch in r:
            assert ch in ".#", f"Only '.' and '#' allowed, got {ch!r}"
    return rows


GLYPHS: Dict[str, List[str]] = {
    # --------------------
    # Uppercase A–Z
    # --------------------
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

    # --------------------
    # Lowercase a–z
    # --------------------
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

    # --------------------
    # Digits 0–9
    # --------------------
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


# ----------------------------
# Primitive SVG symbols
# ----------------------------
def svg_defs() -> str:
    d = D
    r = D / 2
    return f"""  <defs>
    <symbol id="p0" viewBox="0 0 {d} {d}">
      <rect x="0" y="0" width="{d}" height="{d}" fill="currentColor"/>
    </symbol>
    <symbol id="p1" viewBox="0 0 {d} {d}">
      <circle cx="{r:g}" cy="{r:g}" r="{r:g}" fill="currentColor"/>
    </symbol>
    <symbol id="p2" viewBox="0 0 {d} {d}">
      <path d="M {d:g} {d:g} A {r:g} {r:g} 0 0 0 0 {d:g} Z" fill="currentColor"/>
    </symbol>
    <symbol id="p3" viewBox="0 0 {d} {d}">
      <path d="M 0 0 A {r:g} {r:g} 0 0 0 {d:g} 0 Z" fill="currentColor"/>
    </symbol>
    <symbol id="p4" viewBox="0 0 {d} {d}">
      <path d="M 0 {d:g} A {r:g} {r:g} 0 0 0 0 0 Z" fill="currentColor"/>
    </symbol>
    <symbol id="p5" viewBox="0 0 {d} {d}">
      <path d="M {d:g} 0 A {r:g} {r:g} 0 0 0 {d:g} {d:g} Z" fill="currentColor"/>
    </symbol>
    <symbol id="p6" viewBox="0 0 {d} {d}">
      <path d="M {d:g} 0 L {d:g} {d:g} A {d:g} {d:g} 0 0 1 0 0 Z" fill="currentColor"/>
    </symbol>
    <symbol id="p7" viewBox="0 0 {d} {d}">
      <path d="M {d:g} {d:g} L 0 {d:g} A {d:g} {d:g} 0 0 1 {d:g} 0 Z" fill="currentColor"/>
    </symbol>
    <symbol id="p8" viewBox="0 0 {d} {d}">
      <path d="M 0 {d:g} L 0 0 A {d:g} {d:g} 0 0 1 {d:g} {d:g} Z" fill="currentColor"/>
    </symbol>
    <symbol id="p9" viewBox="0 0 {d} {d}">
      <path d="M 0 0 L {d:g} 0 A {d:g} {d:g} 0 0 1 0 {d:g} Z" fill="currentColor"/>
    </symbol>
  </defs>
"""


# ----------------------------
# Bitmap -> primitive selection
# ----------------------------
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

    # isolated -> dot
    if n == 0:
        return 1

    # endpoints -> use a half with FLAT edge facing the neighbor
    if n == 1:
        if dn:  # connects downward => flat bottom to connect
            return 2
        if up:  # connects upward => flat top to connect
            return 3
        if rt:  # connects right => flat right to connect
            return 5
        if lf:  # connects left => flat left to connect
            return 4
        return 0

    # orthogonal corner -> quarter with flats on the connected edges
    if n == 2 and ((up and lf) or (up and rt) or (dn and lf) or (dn and rt)):
        if up and lf:
            return 9  # flat top+left
        if up and rt:
            return 6  # flat top+right
        if dn and lf:
            return 8  # flat bottom+left
        if dn and rt:
            return 7  # flat bottom+right
        return 0

    # straight segments / junctions -> square
    return 0


def rand_rgb() -> str:
    return f"rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)})"


def glyph_to_svg_random_rgb(g: List[str], seed: Optional[int] = None) -> str:
    if seed is not None:
        random.seed(seed)

    w = GRID_W * D
    h = GRID_H * D
    out: List[str] = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    out.append(svg_defs())

    # Each tile gets its own random color via style="color: rgb(...)"
    for y in range(GRID_H):
        for x in range(GRID_W):
            pid = pick_primitive(g, x, y)
            if pid is None:
                continue
            out.append(
                f'  <g transform="translate({x*D},{y*D})" style="color: {rand_rgb()}">'
                f'<use href="#p{pid}" x="0" y="0" width="{D}" height="{D}"/></g>'
            )

    out.append("</svg>\n")
    return "\n".join(out)


# ----------------------------
# Write files
# ----------------------------
def main() -> None:
    script_dir = Path(__file__).resolve().parent  # tools/
    out_dir = script_dir.parent / "sketches" / "alphabet-5x9-manual-rgb"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Uppercase
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        svg = glyph_to_svg_random_rgb(GLYPHS[ch])
        (out_dir / f"upper-{ch}.svg").write_text(svg, encoding="utf-8")

    # Lowercase
    for ch in "abcdefghijklmnopqrstuvwxyz":
        svg = glyph_to_svg_random_rgb(GLYPHS[ch])
        (out_dir / f"lower-{ch}.svg").write_text(svg, encoding="utf-8")

    # Digits
    for ch in "0123456789":
        svg = glyph_to_svg_random_rgb(GLYPHS[ch])
        (out_dir / f"digit-{ch}.svg").write_text(svg, encoding="utf-8")

    print(f"Wrote 62 glyph SVGs (random RGB per tile) to: {out_dir}")


if __name__ == "__main__":
    main()
