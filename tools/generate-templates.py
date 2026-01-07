#!/usr/bin/env python3
"""
Generate per-character template partials for:

- Symfony/Twig:  templates/_character-{codepoint}.svg.twig
- CakePHP:       templates/element/character-{codepoint}.php

Where {codepoint} is like:
  A  -> U0041
  a  -> U0061
  0  -> U0030

Each template outputs a standalone SVG (5×9 tiles, tile=48 => 240×432 viewBox),
and assigns a RANDOM RGB fill per primitive instance at render-time:
- Twig uses:  random(255)
- Cake uses:  random_int(0,255)

Put this script in: tools/
It writes into:      ../templates/ and ../templates/element/
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

GRID_W, GRID_H = 5, 9
D = 48
SVG_W, SVG_H = GRID_W * D, GRID_H * D


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


# ----------------------------
# Bitmap -> primitive IDs
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

    # endpoints -> half with flat edge facing the neighbor
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


def tiles_for_glyph(g: List[str]) -> List[Tuple[int, int, int]]:
    tiles: List[Tuple[int, int, int]] = []
    for y in range(GRID_H):
        for x in range(GRID_W):
            pid = pick_primitive(g, x, y)
            if pid is None:
                continue
            tiles.append((x * D, y * D, pid))
    return tiles


def codepoint_name(ch: str) -> str:
    # 4-hex is perfect for ASCII; still works for higher codepoints (pads only up to 4).
    cp = ord(ch)
    return f"U{cp:04X}" if cp <= 0xFFFF else f"U{cp:06X}"


# ----------------------------
# Shared SVG defs
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
# Template generators
# ----------------------------
def twig_template(codepoint: str, label: str, tiles: List[Tuple[int, int, int]]) -> str:
    # Random RGB per primitive instance at render time (unless randomize=false).
    lines: List[str] = []
    lines.append("{# Auto-generated. Example usage:")
    lines.append("   {{ include('_character-" + codepoint + ".svg.twig', { randomize: true }) }}")
    lines.append("#}")
    lines.append("{% set width = width|default(" + str(SVG_W) + ") %}")
    lines.append("{% set height = height|default(" + str(SVG_H) + ") %}")
    lines.append("{% set class = class|default('') %}")
    lines.append("{% set style = style|default('') %}")
    lines.append("{% set randomize = randomize|default(true) %}")
    lines.append("{% set color = color|default('#000') %}")
    lines.append("")
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{{{{ width }}}}" height="{{{{ height }}}}" '
        f'viewBox="0 0 {SVG_W} {SVG_H}" class="{{{{ class }}}}" style="{{{{ style }}}}" '
        f'role="img" aria-label="{label}" shape-rendering="geometricPrecision">'
    )
    lines.append(svg_defs())
    for x, y, pid in tiles:
        lines.append(
            f'  <g transform="translate({x},{y})" '
            f'style="color: {{{{ randomize ? (\'rgb(\' ~ random(255) ~ \',\' ~ random(255) ~ \',\' ~ random(255) ~ \')\') : color }}}}">'
            f'<use href="#p{pid}" x="0" y="0" width="{D}" height="{D}"/></g>'
        )
    lines.append("</svg>")
    lines.append("")
    return "\n".join(lines)


def cake_template(codepoint: str, label: str, tiles: List[Tuple[int, int, int]]) -> str:
    # Random RGB per primitive instance at render time (unless $randomize=false).
    lines: List[str] = []
    lines.append("<?php")
    lines.append("/**")
    lines.append(" * Auto-generated CakePHP element.")
    lines.append(f" * Render: <?= $this->element('character-{codepoint}', ['randomize' => true]) ?>")
    lines.append(" */")
    lines.append(f"$width = $width ?? {SVG_W};")
    lines.append(f"$height = $height ?? {SVG_H};")
    lines.append("$class = $class ?? '';")
    lines.append("$style = $style ?? '';")
    lines.append("$randomize = $randomize ?? true;")
    lines.append("$color = $color ?? '#000';")
    lines.append("?>")
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="<?= (int)$width ?>" height="<?= (int)$height ?>" '
        f'viewBox="0 0 {SVG_W} {SVG_H}"'
        f'<?= $class !== \'\' ? \' class="\' . h($class) . \'"\' : \'\' ?>'
        f'<?= $style !== \'\' ? \' style="\' . h($style) . \'"\' : \'\' ?>'
        f' role="img" aria-label="{label}" shape-rendering="geometricPrecision">'
    )
    lines.append(svg_defs())
    for x, y, pid in tiles:
        lines.append(
            f'  <g transform="translate({x},{y})" style="color: <?= $randomize '
            f'? (\'rgb(\' . random_int(0,255) . \',\' . random_int(0,255) . \',\' . random_int(0,255) . \')\') '
            f': h($color) ?>"><use href="#p{pid}" x="0" y="0" width="{D}" height="{D}"/></g>'
        )
    lines.append("</svg>")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    script_dir = Path(__file__).resolve().parent      # tools/
    root_dir = script_dir.parent                      # project root (one up)
    twig_dir = root_dir / "templates"                 # Symfony default
    cake_dir = root_dir / "templates" / "element"     # CakePHP default

    twig_dir.mkdir(parents=True, exist_ok=True)
    cake_dir.mkdir(parents=True, exist_ok=True)

    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    for ch in chars:
        cp = codepoint_name(ch)
        label = ch
        tiles = tiles_for_glyph(GLYPHS[ch])

        (twig_dir / f"_character-{cp}.svg.twig").write_text(
            twig_template(codepoint=cp, label=label, tiles=tiles),
            encoding="utf-8",
        )
        (cake_dir / f"character-{cp}.php").write_text(
            cake_template(codepoint=cp, label=label, tiles=tiles),
            encoding="utf-8",
        )

    print(f"Wrote Twig partials to: {twig_dir}")
    print(f"Wrote Cake elements  to: {cake_dir}")


if __name__ == "__main__":
    main()
