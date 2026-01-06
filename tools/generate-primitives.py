#!/usr/bin/env python3
"""
Generate the 10 canvas primitives (d = 48) as standalone SVG files.

Expected layout:
- this script lives in:   tools/
- output goes to:         sketches/   (one directory up from tools/)
"""

from __future__ import annotations

from pathlib import Path


D = 48
OUT_DIRNAME = "sketches"


def wrap_svg(inner: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{D}" height="{D}" viewBox="0 0 {D} {D}">\n'
        f'{inner}\n'
        f"</svg>\n"
    )


def main() -> None:
    script_dir = Path(__file__).resolve().parent          # tools/
    out_dir = script_dir.parent / OUT_DIRNAME             # ../sketches
    out_dir.mkdir(parents=True, exist_ok=True)

    # Fill-only, like your canvas demo.
    fill = 'fill="#000"'

    svgs: dict[str, str] = {
        # p=0 — square
        "primitive-0-square.svg": wrap_svg(
            f'  <rect x="0" y="0" width="{D}" height="{D}" {fill}/>'
        ),

        # p=1 — circle (centered)
        "primitive-1-circle.svg": wrap_svg(
            f'  <circle cx="{D/2:g}" cy="{D/2:g}" r="{D/2:g}" {fill}/>'
        ),

        # p=2 — half circle (bottom; dome up)   center=(24,48), r=24, 0..π, anticlockwise=true
        "primitive-2-half-bottom.svg": wrap_svg(
            f'  <path {fill} d="M {D:g} {D:g} A {D/2:g} {D/2:g} 0 0 0 0 {D:g} Z"/>'
        ),

        # p=3 — half circle (top; dome down)    center=(24,0), r=24, π..2π, anticlockwise=true
        "primitive-3-half-top.svg": wrap_svg(
            f'  <path {fill} d="M 0 0 A {D/2:g} {D/2:g} 0 0 0 {D:g} 0 Z"/>'
        ),

        # p=4 — half circle (left; bulge right) center=(0,24), r=24, π/2..3π/2, anticlockwise=true
        "primitive-4-half-left.svg": wrap_svg(
            f'  <path {fill} d="M 0 {D:g} A {D/2:g} {D/2:g} 0 0 0 0 0 Z"/>'
        ),

        # p=5 — half circle (right; bulge left) center=(48,24), r=24, 3π/2..π/2, anticlockwise=true
        "primitive-5-half-right.svg": wrap_svg(
            f'  <path {fill} d="M {D:g} 0 A {D/2:g} {D/2:g} 0 0 0 {D:g} {D:g} Z"/>'
        ),

        # p=6 — quarter circle (center top-right), r=48, π/2..π, anticlockwise=false
        "primitive-6-quarter-top-right.svg": wrap_svg(
            f'  <path {fill} d="M 0 0 L {D:g} 0 L {D:g} {D:g} A {D:g} {D:g} 0 0 1 0 0 Z"/>'
        ),

        # p=7 — quarter circle (center bottom-right), r=48, π..3π/2, anticlockwise=false
        "primitive-7-quarter-bottom-right.svg": wrap_svg(
            f'  <path {fill} d="M {D:g} 0 L {D:g} {D:g} L 0 {D:g} A {D:g} {D:g} 0 0 1 {D:g} 0 Z"/>'
        ),

        # p=8 — quarter circle (center bottom-left), r=48, 3π/2..2π, anticlockwise=false
        # (Standalone version: keep the path inside the 0..48 viewBox.)
        "primitive-8-quarter-bottom-left.svg": wrap_svg(
            f'  <path {fill} d="M 0 {D:g} L 0 0 A {D:g} {D:g} 0 0 1 {D:g} {D:g} Z"/>'
        ),

        # p=9 — quarter circle (center top-left), r=48, 2π..5π/2, anticlockwise=false
        # (Standalone version: keep the path inside the 0..48 viewBox.)
        "primitive-9-quarter-top-left.svg": wrap_svg(
            f'  <path {fill} d="M 0 0 L {D:g} 0 A {D:g} {D:g} 0 0 1 0 {D:g} Z"/>'
        ),
    }

    for name, svg in svgs.items():
        (out_dir / name).write_text(svg, encoding="utf-8")

    print(f"Wrote {len(svgs)} SVG files to: {out_dir}")


if __name__ == "__main__":
    main()
