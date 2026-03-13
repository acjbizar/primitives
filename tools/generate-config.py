#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC_DIR = ROOT / "src" / "svg"
DEFAULT_CONFIG_OUT = ROOT / "config" / "primitives.php"

RE_NEW_SINGLE = re.compile(r"^character-u([0-9a-fA-F]{1,8})\.svg$")
RE_NEW_LIGA = re.compile(r"^ligature-((?:u[0-9a-fA-F]{1,8})(?:-u[0-9a-fA-F]{1,8})+)\.svg$")
RE_OLD_CHAR = re.compile(r"^character-(.+)\.svg$")


def decode_svg_filename_to_key(filename: str) -> Optional[str]:
    m = RE_NEW_SINGLE.match(filename)
    if m:
        cp = int(m.group(1), 16)
        try:
            return chr(cp)
        except ValueError:
            return None

    m = RE_NEW_LIGA.match(filename)
    if m:
        chars: List[str] = []
        for part in m.group(1).split("-"):
            cp = int(part[1:], 16)  # strip leading "u"
            try:
                chars.append(chr(cp))
            except ValueError:
                return None
        return "".join(chars)

    m = RE_OLD_CHAR.match(filename)
    if m:
        return m.group(1)

    return None


def collect_svg_map(src_dir: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}

    for p in sorted((x for x in src_dir.glob("*.svg") if x.is_file()), key=lambda x: x.name.lower()):
        key = decode_svg_filename_to_key(p.name)
        if not key:
            continue

        existing = out.get(key)
        if existing is None:
            out[key] = p.name
            continue

        is_new = bool(RE_NEW_SINGLE.match(p.name) or RE_NEW_LIGA.match(p.name))
        existing_is_new = bool(RE_NEW_SINGLE.match(existing) or RE_NEW_LIGA.match(existing))
        if is_new and not existing_is_new:
            out[key] = p.name

    return out


def key_sort_tuple(key: str) -> Tuple[int, Tuple[int, ...]]:
    return (len(key), tuple(ord(c) for c in key))


def _is_printable_char(ch: str) -> bool:
    return ch.isprintable() and ch not in {"\n", "\r", "\t", "\x0b", "\x0c"}


def _group_runtime_chars(svg_map: Dict[str, str]) -> Dict[str, Any]:
    singles = sorted(
        (k for k in svg_map.keys() if len(k) == 1 and _is_printable_char(k)),
        key=lambda ch: ord(ch),
    )

    upper: List[str] = []
    lower: List[str] = []
    digits: List[str] = []
    punct: List[str] = []
    other: List[str] = []

    codepoints: List[int] = []
    char_to_filename: Dict[str, str] = {}
    char_to_unicode: Dict[str, str] = {}

    for ch in singles:
        cp = ord(ch)
        codepoints.append(cp)
        char_to_filename[ch] = svg_map[ch]
        char_to_unicode[ch] = f"U+{cp:04X}"

        if "A" <= ch <= "Z":
            upper.append(ch)
        elif "a" <= ch <= "z":
            lower.append(ch)
        elif "0" <= ch <= "9":
            digits.append(ch)
        elif ch.isprintable() and not ch.isalnum() and not ch.isspace():
            punct.append(ch)
        else:
            other.append(ch)

    all_chars = upper + lower + digits + punct + other

    return {
        "all": "".join(all_chars),
        "uppercase": "".join(upper),
        "lowercase": "".join(lower),
        "digits": "".join(digits),
        "punct": "".join(punct),
        "other": "".join(other),
        "codepoints": codepoints,
        "charToFilename": char_to_filename,
        "charToUnicode": char_to_unicode,
    }


def _codepoints_to_ranges(codepoints: List[int]) -> List[List[int]]:
    if not codepoints:
        return []

    cps = sorted(set(codepoints))
    ranges: List[List[int]] = []

    start = prev = cps[0]
    for cp in cps[1:]:
        if cp == prev + 1:
            prev = cp
            continue
        ranges.append([start, prev])
        start = prev = cp
    ranges.append([start, prev])

    return ranges


def _php_scalar(value: Any, indent: int = 0) -> str:
    pad = " " * indent
    next_pad = " " * (indent + 4)

    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        escaped = (
            value.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\r", "\\r")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
        return f"'{escaped}'"

    if isinstance(value, list):
        if not value:
            return "[]"
        lines = ["["]
        for item in value:
            lines.append(f"{next_pad}{_php_scalar(item, indent + 4)},")
        lines.append(f"{pad}]")
        return "\n".join(lines)

    if isinstance(value, dict):
        if not value:
            return "[]"
        lines = ["["]
        for k, v in value.items():
            lines.append(f"{next_pad}{_php_scalar(str(k))} => {_php_scalar(v, indent + 4)},")
        lines.append(f"{pad}]")
        return "\n".join(lines)

    raise TypeError(f"Unsupported value for PHP export: {type(value)!r}")


def build_cake_config_payload(svg_map: Dict[str, str]) -> Dict[str, Any]:
    runtime = _group_runtime_chars(svg_map)
    codepoints = runtime["codepoints"]
    unicode_ranges = _codepoints_to_ranges(codepoints)

    ligature_keys = sorted([k for k in svg_map.keys() if len(k) > 1], key=key_sort_tuple)

    ligatures: Dict[str, Dict[str, Any]] = {}
    for key in ligature_keys:
        ligatures[key] = {
            "sequence": key,
            "chars": list(key),
            "codepoints": [ord(ch) for ch in key],
            "unicode": [f"U+{ord(ch):04X}" for ch in key],
            "filename": svg_map[key],
        }

    glyphs: Dict[str, Dict[str, Any]] = {}
    for key in sorted(svg_map.keys(), key=key_sort_tuple):
        glyphs[key] = {
            "key": key,
            "filename": svg_map[key],
            "isLigature": len(key) > 1,
            "length": len(key),
            "chars": list(key),
            "codepoints": [ord(ch) for ch in key],
            "unicode": [f"U+{ord(ch):04X}" for ch in key],
        }

    return {
        "Primitives": {
            "glyphCount": len(svg_map),
            "singleGlyphCount": sum(1 for k in svg_map if len(k) == 1),
            "ligatureCount": sum(1 for k in svg_map if len(k) > 1),

            "chars": runtime["all"],
            "uppercase": runtime["uppercase"],
            "lowercase": runtime["lowercase"],
            "digits": runtime["digits"],
            "punct": runtime["punct"],
            "other": runtime["other"],

            "codepoints": codepoints,
            "unicodeRanges": unicode_ranges,

            "charToFilename": runtime["charToFilename"],
            "charToUnicode": runtime["charToUnicode"],

            "ligatureKeys": ligature_keys,
            "ligatures": ligatures,

            "svgMap": dict(sorted(svg_map.items(), key=lambda kv: key_sort_tuple(kv[0]))),
            "glyphs": glyphs,

            "hasUppercase": bool(runtime["uppercase"]),
            "hasLowercase": bool(runtime["lowercase"]),
            "hasDigits": bool(runtime["digits"]),
            "hasPunct": bool(runtime["punct"]),
        }
    }


def write_cake_config(svg_map: Dict[str, str], out_path: Path) -> None:
    payload = build_cake_config_payload(svg_map)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    content = (
        "<?php\n"
        "declare(strict_types=1);\n\n"
        "// Auto-generated by tools/generate-config.py\n"
        "// Runtime-friendly config for CakePHP/plugin usage.\n\n"
        "return "
        + _php_scalar(payload, 0)
        + ";\n"
    )
    out_path.write_text(content, encoding="utf-8")


def main() -> None:
    src_dir = DEFAULT_SRC_DIR
    out_path = DEFAULT_CONFIG_OUT

    svg_map = collect_svg_map(src_dir)
    if not svg_map:
        raise SystemExit(
            f"No supported SVG glyph files found in {src_dir} "
            "(expected character-uXXXX.svg / ligature-uXXXX-uYYYY.svg / legacy character-*.svg)"
        )

    write_cake_config(svg_map, out_path)

    single_count = sum(1 for k in svg_map if len(k) == 1)
    liga_count = sum(1 for k in svg_map if len(k) > 1)

    print(f"Wrote CakePHP config: {out_path}")
    print(f"Indexed {len(svg_map)} glyphs from {src_dir} ({single_count} single, {liga_count} ligatures)")


if __name__ == "__main__":
    main()