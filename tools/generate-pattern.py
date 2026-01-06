#!/usr/bin/env python3
"""
Generate a 1152×1152 SVG pattern filled with random primitives and random RGB fills.

- This script is intended to live in:   tools/
- Output will be written to:             ../sketches/pattern-{timestamp}.svg
- Primitives are the 10 variants you described (d=48):
  - square, circle
  - 4 half-circles (top/bottom/left/right) with r=24
  - 4 quarter-circles (at each corner) with r=48

Run:
  python tools/generate_pattern.py
"""

from __future__ import annotations

import random
import time
from pathlib import Path

D = 48
W = 1152
H = 1152

COLS = W // D  # 24
ROWS = H // D  # 24


def svg_defs() -> str:
    # Each symbol uses fill="currentColor" so each <use> can set CSS `color: rgb(...)`.
    return f"""  <defs>
    <symbol id="p0" viewBox="0 0 {D} {D}">
      <rect x="0" y="0" width="{D}" height="{D}" fill="currentColor"/>
    </symbol>

    <symbol id="p1" viewBox="0 0 {D} {D}">
      <circle cx="{D/2:g}" cy="{D/2:g}" r="{D/2:g}" fill="currentColor"/>
    </symbol>

    <!-- half circles (r = 24) -->
    <symbol id="p2" viewBox="0 0 {D} {D}">
      <!-- bottom (dome up) -->
      <path d="M {D:g} {D:g} A {D/2:g} {D/2:g} 0 0 0 0 {D:g} Z" fill="currentColor"/>
    </symbol>

    <symbol id="p3" viewBox="0 0 {D} {D}">
      <!-- top (dome down) -->
      <path d="M 0 0 A {D/2:g} {D/2:g} 0 0 0 {D:g} 0 Z" fill="currentColor"/>
    </symbol>

    <symbol id="p4" viewBox="0 0 {D} {D}">
      <!-- left (bulge right) -->
      <path d="M 0 {D:g} A {D/2:g} {D/2:g} 0 0 0 0 0 Z" fill="currentColor"/>
    </symbol>

    <symbol id="p5" viewBox="0 0 {D} {D}">
      <!-- right (bulge left) -->
      <path d="M {D:g} 0 A {D/2:g} {D/2:g} 0 0 0 {D:g} {D:g} Z" fill="currentColor"/>
    </symbol>

    <!-- quarter circles (r = 48) at the corners -->
    <symbol id="p6" viewBox="0 0 {D} {D}">
      <!-- top-right (center at 48,0) -->
      <path d="M {D:g} 0 L {D:g} {D:g} A {D:g} {D:g} 0 0 1 0 0 Z" fill="currentColor"/>
    </symbol>

    <symbol id="p7" viewBox="0 0 {D} {D}">
      <!-- bottom-right (center at 48,48) -->
      <path d="M {D:g} {D:g} L 0 {D:g} A {D:g} {D:g} 0 0 1 {D:g} 0 Z" fill="currentColor"/>
    </symbol>

    <symbol id="p8" viewBox="0 0 {D} {D}">
      <!-- bottom-left (center at 0,48) -->
      <path d="M 0 {D:g} L 0 0 A {D:g} {D:g} 0 0 1 {D:g} {D:g} Z" fill="currentColor"/>
    </symbol>

    <symbol id="p9" viewBox="0 0 {D} {D}">
      <!-- top-left (center at 0,0) -->
      <path d="M 0 0 L {D:g} 0 A {D:g} {D:g} 0 0 1 0 {D:g} Z" fill="currentColor"/>
    </symbol>
  </defs>
"""


def main() -> None:
    script_dir = Path(__file__).resolve().parent  # tools/
    out_dir = script_dir.parent / "sketches"      # ../sketches
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time() * 1000)  # ms since epoch
    out_path = out_dir / f"pattern-{timestamp}.svg"

    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    parts.append(svg_defs())

    # Optional: keep edges sharp-ish if you ever rasterize
    parts.append('  <g shape-rendering="geometricPrecision">')

    for r in range(ROWS):
        y = r * D
        for c in range(COLS):
            x = c * D
            p = random.randint(0, 9)
            rr = random.randint(0, 255)
            gg = random.randint(0, 255)
            bb = random.randint(0, 255)

            # Using currentColor -> set per-instance via CSS color
            parts.append(
                f'    <use href="#p{p}" x="{x}" y="{y}" width="{D}" height="{D}" '
                f'style="color: rgb({rr},{gg},{bb})" />'
            )

    parts.append("  </g>")
    parts.append("</svg>\n")

    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
