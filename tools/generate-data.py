#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/generate-data.py

Parse primitive-based glyph SVGs from:
  src/svg/character-u{codepoint}.svg

And generate:
  data/glyphs.json
  data/glyphs.py

Expected SVG structure (from your glyph designer / generator):
- <defs> containing symbols p0..p9
- glyph tiles placed as:
    <g transform="translate(X,Y)" style="color: ...">
      <use href="#pN" x="0" y="0" width="{D}" height="{D}"/>
    </g>

What gets extracted:
- codepoint metadata (single or multi codepoint)
- inferred tile size (D)
- grid width/height
- bitmap rows ('.' / '#')
- primitive grid (None or 0..9)
- color grid (None or color string)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, Iterable, List, Optional, Tuple
import xml.etree.ElementTree as ET


# ------------------------------------------------------------
# Defaults (script lives in tools/)
# ------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DEFAULT_SRC_DIR = PROJECT_ROOT / "src" / "svg"
DEFAULT_OUT_JSON = PROJECT_ROOT / "data" / "glyphs.json"
DEFAULT_OUT_PY = PROJECT_ROOT / "data" / "glyphs.py"
DEFAULT_PATTERN = "character-u*.svg"

FILENAME_RE = re.compile(
    r"^character-u(?P<hexes>[0-9a-fA-F]+(?:-[0-9a-fA-F]+)*)\.svg$"
)

TRANSLATE_RE = re.compile(
    r"translate\(\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"(?:[\s,]+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?))?\s*\)"
)

PRIMITIVE_HREF_RE = re.compile(r"#p([0-9])$")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def local_name(tag: str) -> str:
    """Strip XML namespace from a tag."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def parse_style(style: Optional[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not style:
        return out
    for part in style.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        k, v = part.split(":", 1)
        out[k.strip().lower()] = v.strip()
    return out


def parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    s = value.strip()
    if not s:
        return None
    # Strip simple unit suffixes like "48px"
    m = re.match(r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([a-zA-Z%]*)$", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def parse_viewbox(root: ET.Element) -> Optional[Tuple[float, float, float, float]]:
    vb = root.get("viewBox")
    if not vb:
        return None
    parts = vb.replace(",", " ").split()
    if len(parts) != 4:
        return None
    try:
        x, y, w, h = map(float, parts)
        return x, y, w, h
    except ValueError:
        return None


def parse_translate(transform: Optional[str]) -> Tuple[float, float]:
    if not transform:
        return 0.0, 0.0
    m = TRANSLATE_RE.search(transform)
    if not m:
        return 0.0, 0.0
    x = float(m.group(1))
    y = float(m.group(2)) if m.group(2) is not None else 0.0
    return x, y


def parse_codepoints_from_filename(path: Path) -> List[int]:
    m = FILENAME_RE.match(path.name)
    if not m:
        raise ValueError(f"Filename does not match expected pattern: {path.name}")
    hexes = m.group("hexes").split("-")
    cps = [int(h, 16) for h in hexes]
    return cps


def codepoint_key(cps: Iterable[int]) -> str:
    return "-".join(f"{cp:04x}" for cp in cps)


def codepoints_to_text(cps: List[int]) -> str:
    chars = []
    for cp in cps:
        try:
            chars.append(chr(cp))
        except ValueError:
            # Invalid Unicode scalar; keep placeholder
            chars.append("\uFFFD")
    return "".join(chars)


def json_safe_float(n: float) -> int | float:
    # Emit ints when possible for cleaner output
    if abs(n - round(n)) < 1e-9:
        return int(round(n))
    return n


# ------------------------------------------------------------
# SVG parsing
# ------------------------------------------------------------
@dataclass
class ParsedTile:
    x_px: float
    y_px: float
    primitive: int
    color: Optional[str]
    use_w: Optional[float]
    use_h: Optional[float]


def find_first_use_in_group(g: ET.Element) -> Optional[ET.Element]:
    # Generated files use direct <use>, but descend just in case
    for node in g.iter():
        if local_name(node.tag) == "use":
            return node
    return None


def find_symbol_tile_size(root: ET.Element) -> Optional[float]:
    # Fallback if <use width/height> is missing
    for node in root.iter():
        if local_name(node.tag) != "symbol":
            continue
        sid = node.get("id")
        if sid != "p0":
            continue
        vb = node.get("viewBox")
        if not vb:
            continue
        parts = vb.replace(",", " ").split()
        if len(parts) != 4:
            continue
        try:
            _, _, w, h = map(float, parts)
        except ValueError:
            continue
        if w > 0 and h > 0 and abs(w - h) < 1e-6:
            return w
    return None


def parse_svg_tiles(svg_path: Path) -> Tuple[ET.Element, List[ParsedTile]]:
    root = ET.parse(svg_path).getroot()
    tiles: List[ParsedTile] = []

    for node in root.iter():
        if local_name(node.tag) != "g":
            continue

        use = find_first_use_in_group(node)
        if use is None:
            continue

        href = (
            use.get("href")
            or use.get("{http://www.w3.org/1999/xlink}href")
            or ""
        ).strip()
        m = PRIMITIVE_HREF_RE.search(href)
        if not m:
            continue

        primitive = int(m.group(1))

        tx, ty = parse_translate(node.get("transform"))
        ux = parse_float(use.get("x")) or 0.0
        uy = parse_float(use.get("y")) or 0.0
        w = parse_float(use.get("width"))
        h = parse_float(use.get("height"))

        # Color can live on <g> via style="color: ...", or directly as attrs
        style_map = parse_style(node.get("style"))
        color = (
            style_map.get("color")
            or node.get("color")
            or parse_style(use.get("style")).get("color")
            or use.get("color")
        )

        tiles.append(
            ParsedTile(
                x_px=tx + ux,
                y_px=ty + uy,
                primitive=primitive,
                color=color,
                use_w=w,
                use_h=h,
            )
        )

    return root, tiles


def infer_tile_size(root: ET.Element, tiles: List[ParsedTile], svg_path: Path) -> float:
    # Prefer width/height on <use>
    dims: List[float] = []
    for t in tiles:
        if t.use_w is not None:
            dims.append(t.use_w)
        if t.use_h is not None:
            dims.append(t.use_h)

    if dims:
        rounded = [round(d, 6) for d in dims if d and d > 0]
        if rounded:
            most_common, _ = Counter(rounded).most_common(1)[0]
            return float(most_common)

    # Fallback: p0 symbol viewBox
    symbol_d = find_symbol_tile_size(root)
    if symbol_d:
        return symbol_d

    raise ValueError(f"Could not infer tile size for {svg_path}")


def infer_grid_size(
    root: ET.Element,
    tiles: List[ParsedTile],
    tile_size: float,
    svg_path: Path,
) -> Tuple[int, int, Optional[List[int | float]]]:
    vb = parse_viewbox(root)
    view_box_out: Optional[List[int | float]] = None

    if vb:
        vx, vy, vw, vh = vb
        view_box_out = [json_safe_float(vx), json_safe_float(vy), json_safe_float(vw), json_safe_float(vh)]
        cols_f = vw / tile_size
        rows_f = vh / tile_size
        cols = int(round(cols_f))
        rows = int(round(rows_f))
        if cols <= 0 or rows <= 0:
            raise ValueError(f"Invalid grid inferred from viewBox in {svg_path}")
        if abs(cols_f - cols) > 1e-5 or abs(rows_f - rows) > 1e-5:
            raise ValueError(
                f"viewBox is not an integer multiple of tile size in {svg_path}: "
                f"viewBox={vw}x{vh}, tile={tile_size}"
            )
        return cols, rows, view_box_out

    # Fallback from tiles only
    if not tiles:
        raise ValueError(f"No tiles and no viewBox; cannot infer grid size for {svg_path}")

    xs = [int(round(t.x_px / tile_size)) for t in tiles]
    ys = [int(round(t.y_px / tile_size)) for t in tiles]
    cols = max(xs) + 1
    rows = max(ys) + 1
    return cols, rows, None


def grid_indices_from_tiles(
    tiles: List[ParsedTile],
    tile_size: float,
    cols: int,
    rows: int,
    svg_path: Path,
) -> Tuple[List[List[Optional[int]]], List[List[Optional[str]]]]:
    primitive_grid: List[List[Optional[int]]] = [[None for _ in range(cols)] for _ in range(rows)]
    color_grid: List[List[Optional[str]]] = [[None for _ in range(cols)] for _ in range(rows)]

    for t in tiles:
        xf = t.x_px / tile_size
        yf = t.y_px / tile_size
        x = int(round(xf))
        y = int(round(yf))

        if abs(xf - x) > 1e-5 or abs(yf - y) > 1e-5:
            raise ValueError(
                f"Tile translate not aligned to grid in {svg_path}: "
                f"({t.x_px},{t.y_px}) with tile {tile_size}"
            )

        if not (0 <= x < cols and 0 <= y < rows):
            raise ValueError(f"Tile out of bounds in {svg_path}: ({x},{y}) for grid {cols}x{rows}")

        if primitive_grid[y][x] is not None:
            raise ValueError(f"Duplicate tile at ({x},{y}) in {svg_path}")

        primitive_grid[y][x] = t.primitive
        color_grid[y][x] = t.color

    return primitive_grid, color_grid


def bitmap_from_primitive_grid(primitive_grid: List[List[Optional[int]]]) -> List[str]:
    return [
        "".join("#" if cell is not None else "." for cell in row)
        for row in primitive_grid
    ]


# ------------------------------------------------------------
# Build records
# ------------------------------------------------------------
def build_record(svg_path: Path) -> Dict[str, Any]:
    cps = parse_codepoints_from_filename(svg_path)
    cp_key = codepoint_key(cps)
    text_value = codepoints_to_text(cps)

    root, tiles = parse_svg_tiles(svg_path)
    tile_size = infer_tile_size(root, tiles, svg_path)
    cols, rows, view_box = infer_grid_size(root, tiles, tile_size, svg_path)
    primitive_grid, color_grid = grid_indices_from_tiles(tiles, tile_size, cols, rows, svg_path)
    bitmap = bitmap_from_primitive_grid(primitive_grid)

    # Compact tile list (handy for reconstructing original SVG quickly)
    tile_list: List[Dict[str, Any]] = []
    for y, row in enumerate(primitive_grid):
        for x, p in enumerate(row):
            if p is None:
                continue
            tile_list.append(
                {
                    "x": x,
                    "y": y,
                    "primitive": p,
                    "color": color_grid[y][x],
                }
            )

    rec: Dict[str, Any] = OrderedDict()
    rec["filename"] = svg_path.name
    rec["codepoint_key"] = cp_key
    rec["codepoints"] = cps
    rec["codepoints_hex"] = [f"{cp:04x}" for cp in cps]
    rec["text"] = text_value
    rec["grid_w"] = cols
    rec["grid_h"] = rows
    rec["tile_size"] = json_safe_float(tile_size)
    if view_box is not None:
        rec["view_box"] = view_box
    rec["bitmap"] = bitmap
    rec["primitive_grid"] = primitive_grid
    rec["color_grid"] = color_grid
    rec["tiles"] = tile_list

    return rec


def sort_svg_paths(paths: Iterable[Path]) -> List[Path]:
    def sort_key(p: Path) -> Tuple[List[int], str]:
        try:
            cps = parse_codepoints_from_filename(p)
        except Exception:
            cps = [sys.maxsize]
        return (cps, p.name.lower())

    return sorted(paths, key=sort_key)


# ------------------------------------------------------------
# Output writers
# ------------------------------------------------------------
def write_json(
    out_json: Path,
    records_by_codepoint: "OrderedDict[str, Dict[str, Any]]",
) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)

    char_index: Dict[str, str] = {}
    for cp_key, rec in records_by_codepoint.items():
        cps = rec["codepoints"]
        if len(cps) == 1:
            ch = rec["text"]
            # Avoid overwriting if duplicates exist
            if ch not in char_index:
                char_index[ch] = cp_key

    payload = OrderedDict()
    payload["meta"] = OrderedDict(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_pattern="src/svg/character-u*.svg",
        glyph_count=len(records_by_codepoint),
        format_version=1,
    )
    payload["char_index"] = char_index
    payload["glyphs_by_codepoint"] = records_by_codepoint

    out_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_python(
    out_py: Path,
    records_by_codepoint: "OrderedDict[str, Dict[str, Any]]",
) -> None:
    out_py.parent.mkdir(parents=True, exist_ok=True)

    glyphs_by_char: "OrderedDict[str, List[str]]" = OrderedDict()
    char_to_codepoint: "OrderedDict[str, str]" = OrderedDict()
    codepoint_to_char: "OrderedDict[str, str]" = OrderedDict()

    for cp_key, rec in records_by_codepoint.items():
        cps = rec["codepoints"]
        if len(cps) == 1:
            ch = rec["text"]
            codepoint_to_char[cp_key] = ch
            if ch not in glyphs_by_char:
                glyphs_by_char[ch] = rec["bitmap"]
                char_to_codepoint[ch] = cp_key

    generated_at = datetime.now(timezone.utc).isoformat()

    header = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/glyphs.py

Auto-generated by tools/generate-data.py
Generated at: {generated_at}

Contents:
- GLYPHS: simple bitmap rows keyed by single-character strings (e.g. "A", "a", "0")
- CHAR_TO_CODEPOINT: maps "A" -> "0041"
- CODEPOINT_TO_CHAR: maps "0041" -> "A"
- GLYPH_DATA: full parsed data keyed by codepoint key (e.g. "0041", "0066-0069")
"""

from __future__ import annotations

'''

    body_parts: List[str] = [header]

    body_parts.append(
        "GLYPHS = " + pformat(dict(glyphs_by_char), width=120, sort_dicts=False) + "\n\n"
    )
    body_parts.append(
        "CHAR_TO_CODEPOINT = " + pformat(dict(char_to_codepoint), width=120, sort_dicts=False) + "\n\n"
    )
    body_parts.append(
        "CODEPOINT_TO_CHAR = " + pformat(dict(codepoint_to_char), width=120, sort_dicts=False) + "\n\n"
    )
    body_parts.append(
        "GLYPH_DATA = " + pformat(dict(records_by_codepoint), width=120, sort_dicts=False) + "\n"
    )

    out_py.write_text("".join(body_parts), encoding="utf-8")


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate data/glyphs.json and data/glyphs.py from src/svg/character-u*.svg"
    )
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC_DIR, help=f"Source SVG directory (default: {DEFAULT_SRC_DIR})")
    ap.add_argument("--pattern", default=DEFAULT_PATTERN, help=f"Glob pattern (default: {DEFAULT_PATTERN})")
    ap.add_argument("--json", dest="out_json", type=Path, default=DEFAULT_OUT_JSON, help=f"Output JSON path (default: {DEFAULT_OUT_JSON})")
    ap.add_argument("--py", dest="out_py", type=Path, default=DEFAULT_OUT_PY, help=f"Output Python path (default: {DEFAULT_OUT_PY})")
    args = ap.parse_args()

    src_dir: Path = args.src
    if not src_dir.exists():
        print(f"Source directory does not exist: {src_dir}", file=sys.stderr)
        return 1

    svg_paths = sort_svg_paths(src_dir.glob(args.pattern))
    if not svg_paths:
        print(f"No SVG files found in {src_dir} matching {args.pattern}", file=sys.stderr)
        return 1

    records_by_codepoint: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    errors: List[str] = []

    for svg_path in svg_paths:
        try:
            rec = build_record(svg_path)
            cp_key = rec["codepoint_key"]
            if cp_key in records_by_codepoint:
                raise ValueError(f"Duplicate codepoint key from filename: {cp_key}")
            records_by_codepoint[cp_key] = rec
        except Exception as e:
            errors.append(f"{svg_path.name}: {e}")

    if errors:
        print("Errors while parsing SVGs:", file=sys.stderr)
        for msg in errors:
            print(f"  - {msg}", file=sys.stderr)
        return 1

    write_json(args.out_json, records_by_codepoint)
    write_python(args.out_py, records_by_codepoint)

    print(f"Wrote {len(records_by_codepoint)} glyphs")
    print(f"  JSON: {args.out_json}")
    print(f"  PY:   {args.out_py}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())