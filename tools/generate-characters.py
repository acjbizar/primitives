#!/usr/bin/env python3
"""
Generate 5×9 (tiles) SVG glyphs for A–Z and a–z using only the 10 primitives.

- Script location: tools/
- Output location: ../sketches/alphabet-5x9/
- Filenames are Windows-safe (no A.svg vs a.svg collisions):
    upper-A.svg ... upper-Z.svg
    lower-a.svg ... lower-z.svg

Requires:
  pip install pillow
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple, Optional

# --- config ---
GRID_W, GRID_H = 5, 9      # tiles
D = 48                     # tile size in SVG units
OS = 64                    # oversample pixels per tile for rasterization (higher => smoother sampling)
THRESH = 0.22              # occupancy threshold per tile (0..1)
MARGIN = 0.08              # margin as fraction of render canvas (0..0.3 is reasonable)

# --- pillow import ---
try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
except Exception:
    print("Error: Pillow is required. Install with: pip install pillow", file=sys.stderr)
    sys.exit(1)


def _candidate_font_paths() -> List[Path]:
    # Try a few common fonts on Linux/macOS/Windows.
    candidates = [
        # Linux
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
        # macOS
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Courier New.ttf"),
        # Windows
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\cour.ttf"),
        Path(r"C:\Windows\Fonts\consola.ttf"),
        Path(r"C:\Windows\Fonts\calibri.ttf"),
    ]
    return candidates


def load_font(size: int, font_path: Optional[Path] = None) -> ImageFont.FreeTypeFont:
    if font_path is not None:
        return ImageFont.truetype(str(font_path), size=size)

    for p in _candidate_font_paths():
        if p.exists():
            return ImageFont.truetype(str(p), size=size)

    # Last resort: try name-based lookup (works on some systems)
    for name in ["DejaVuSans.ttf", "DejaVuSansMono.ttf", "Arial.ttf", "LiberationSans-Regular.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            pass

    raise RuntimeError(
        "Could not find a usable TTF font. "
        "Edit _candidate_font_paths() or pass an explicit font path."
    )


def fit_font_for_char(ch: str, canvas_w: int, canvas_h: int, font_path: Optional[Path]) -> ImageFont.FreeTypeFont:
    # Find a font size that fits within a padded box.
    target_w = int(canvas_w * (1.0 - 2.0 * MARGIN))
    target_h = int(canvas_h * (1.0 - 2.0 * MARGIN))

    # Start big; shrink until it fits.
    size = int(canvas_h * 0.95)
    size = max(size, 16)

    while size > 16:
        font = load_font(size, font_path=font_path)
        bbox = font.getbbox(ch)  # (x0,y0,x1,y1)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        if bw <= target_w and bh <= target_h:
            return font
        size = int(size * 0.92)

    return load_font(16, font_path=font_path)


def raster_to_grid(ch: str, font_path: Optional[Path]) -> List[List[bool]]:
    canvas_w = GRID_W * OS
    canvas_h = GRID_H * OS

    img = Image.new("L", (canvas_w, canvas_h), 0)  # black background
    draw = ImageDraw.Draw(img)

    font = fit_font_for_char(ch, canvas_w, canvas_h, font_path)

    bbox = font.getbbox(ch)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]

    # Center the glyph (bbox may have negative offsets).
    x = (canvas_w - bw) // 2 - bbox[0]
    y = (canvas_h - bh) // 2 - bbox[1]

    draw.text((x, y), ch, fill=255, font=font)

    grid: List[List[bool]] = [[False for _ in range(GRID_W)] for __ in range(GRID_H)]
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            x0, y0 = gx * OS, gy * OS
            tile = img.crop((x0, y0, x0 + OS, y0 + OS))
            mean = sum(tile.getdata()) / (OS * OS * 255.0)
            grid[gy][gx] = mean >= THRESH

    return grid


def pick_primitive(grid: List[List[bool]], x: int, y: int) -> Optional[int]:
    if not grid[y][x]:
        return None

    def on(xx: int, yy: int) -> bool:
        return 0 <= xx < GRID_W and 0 <= yy < GRID_H and grid[yy][xx]

    up = on(x, y - 1)
    dn = on(x, y + 1)
    lf = on(x - 1, y)
    rt = on(x + 1, y)
    n = int(up) + int(dn) + int(lf) + int(rt)

    # isolated dot -> circle
    if n == 0:
        return 1

    # caps -> half circles
    if n == 1:
        if dn:
            return 3  # top cap (half-top)
        if up:
            return 2  # bottom cap (half-bottom)
        if rt:
            return 4  # left cap (half-left)
        if lf:
            return 5  # right cap (half-right)
        return 0

    # corners -> quarter circles at the "outside" corner
    if n == 2 and ((up and lf) or (up and rt) or (dn and lf) or (dn and rt)):
        if (not up) and (not lf):
            return 9  # outside is top-left
        if (not up) and (not rt):
            return 6  # outside is top-right
        if (not dn) and (not lf):
            return 8  # outside is bottom-left
        if (not dn) and (not rt):
            return 7  # outside is bottom-right
        return 0

    # everything else -> square
    return 0


def svg_defs() -> str:
    # currentColor lets us set fill per glyph (or per tile if you want later)
    d = D
    r = D / 2
    return f"""  <defs>
    <symbol id="p0" viewBox="0 0 {d} {d}">
      <rect x="0" y="0" width="{d}" height="{d}" fill="currentColor"/>
    </symbol>

    <symbol id="p1" viewBox="0 0 {d} {d}">
      <circle cx="{r:g}" cy="{r:g}" r="{r:g}" fill="currentColor"/>
    </symbol>

    <!-- half circles (r = 24) -->
    <symbol id="p2" viewBox="0 0 {d} {d}">
      <!-- bottom (dome up), center=(24,48), r=24 -->
      <path d="M {d:g} {d:g} A {r:g} {r:g} 0 0 0 0 {d:g} Z" fill="currentColor"/>
    </symbol>

    <symbol id="p3" viewBox="0 0 {d} {d}">
      <!-- top (dome down), center=(24,0), r=24 -->
      <path d="M 0 0 A {r:g} {r:g} 0 0 0 {d:g} 0 Z" fill="currentColor"/>
    </symbol>

    <symbol id="p4" viewBox="0 0 {d} {d}">
      <!-- left (bulge right), center=(0,24), r=24 -->
      <path d="M 0 {d:g} A {r:g} {r:g} 0 0 0 0 0 Z" fill="currentColor"/>
    </symbol>

    <symbol id="p5" viewBox="0 0 {d} {d}">
      <!-- right (bulge left), center=(48,24), r=24 -->
      <path d="M {d:g} 0 A {r:g} {r:g} 0 0 0 {d:g} {d:g} Z" fill="currentColor"/>
    </symbol>

    <!-- quarter circles (r = 48) -->
    <symbol id="p6" viewBox="0 0 {d} {d}">
      <!-- top-right (center at 48,0) -->
      <path d="M {d:g} 0 L {d:g} {d:g} A {d:g} {d:g} 0 0 1 0 0 Z" fill="currentColor"/>
    </symbol>

    <symbol id="p7" viewBox="0 0 {d} {d}">
      <!-- bottom-right (center at 48,48) -->
      <path d="M {d:g} {d:g} L 0 {d:g} A {d:g} {d:g} 0 0 1 {d:g} 0 Z" fill="currentColor"/>
    </symbol>

    <symbol id="p8" viewBox="0 0 {d} {d}">
      <!-- bottom-left (center at 0,48) -->
      <path d="M 0 {d:g} L 0 0 A {d:g} {d:g} 0 0 1 {d:g} {d:g} Z" fill="currentColor"/>
    </symbol>

    <symbol id="p9" viewBox="0 0 {d} {d}">
      <!-- top-left (center at 0,0) -->
      <path d="M 0 0 L {d:g} 0 A {d:g} {d:g} 0 0 1 0 {d:g} Z" fill="currentColor"/>
    </symbol>
  </defs>
"""


def grid_to_svg(grid: List[List[bool]], fill_color: str = "#000") -> str:
    w = GRID_W * D
    h = GRID_H * D
    parts: List[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    parts.append(svg_defs())
    parts.append(f'  <g style="color: {fill_color}">')
    for y in range(GRID_H):
        for x in range(GRID_W):
            pid = pick_primitive(grid, x, y)
            if pid is None:
                continue
            px = x * D
            py = y * D
            parts.append(f'    <use href="#p{pid}" x="{px}" y="{py}" width="{D}" height="{D}" />')
    parts.append("  </g>")
    parts.append("</svg>\n")
    return "\n".join(parts)


def main() -> None:
    script_dir = Path(__file__).resolve().parent        # tools/
    out_dir = script_dir.parent / "sketches" / "alphabet-5x9"
    out_dir.mkdir(parents=True, exist_ok=True)

    # If you want to force a specific font, set it here:
    #   font_path = Path("path/to/font.ttf")
    font_path: Optional[Path] = None

    # Uppercase
    for code in range(ord("A"), ord("Z") + 1):
        ch = chr(code)
        grid = raster_to_grid(ch, font_path=font_path)
        svg = grid_to_svg(grid, fill_color="#000")
        (out_dir / f"upper-{ch}.svg").write_text(svg, encoding="utf-8")

    # Lowercase
    for code in range(ord("a"), ord("z") + 1):
        ch = chr(code)
        grid = raster_to_grid(ch, font_path=font_path)
        svg = grid_to_svg(grid, fill_color="#000")
        (out_dir / f"lower-{ch}.svg").write_text(svg, encoding="utf-8")

    print(f"Wrote 52 glyph SVGs to: {out_dir}")


if __name__ == "__main__":
    main()
