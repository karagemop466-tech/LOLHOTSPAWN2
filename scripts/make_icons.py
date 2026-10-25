#!/usr/bin/env python3
"""Generate the static home-screen icons used by `docs/manifest.webmanifest`.

Why this exists
---------------
The dashboard is phone-first, but until 2026-10-25 it could not be added to a
phone home screen as a proper app (no manifest, no apple-touch-icon), so a
visitor had to re-find the picks list in a browser every time. These icons are
generated from code — no third-party image, no licence question — so the asset
can be rebuilt byte-for-byte:

    python3 scripts/make_icons.py

Design: the brand blue field with a white target ring + centre dot ("picks").
Pure standard library (zlib + struct), no Pillow dependency.

The output files are committed because GitHub Pages serves them directly; this
script is the source of record for how they were produced.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

BRAND = (11, 95, 255)      # #0b5fff — matches <meta name="theme-color">
WHITE = (255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)
OUT = Path(__file__).resolve().parent.parent / "docs" / "assets"


def _blend(fg, bg, alpha):
    return tuple(round(f * alpha + b * (1 - alpha)) for f, b in zip(fg[:3], bg[:3]))


def render(size: int, *, maskable: bool = False) -> bytes:
    """Return RGBA PNG bytes for a square icon of `size` px.

    maskable=True keeps the artwork inside the 80 % safe zone Chrome requires
    for adaptive icons; the rounded-corner cut-out is only used for the
    non-maskable variants (a maskable icon must fill the whole square).
    """
    cx = cy = size / 2.0
    radius = size * (0.30 if maskable else 0.34)   # outer ring radius
    ring_w = size * 0.055                          # ring stroke
    dot_r = size * 0.105                           # centre dot
    corner = size * 0.22 if not maskable else 0.0  # corner rounding
    scale = 4                                      # supersampling for smooth edges

    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            acc = [0.0, 0.0, 0.0, 0.0]
            for sy in range(scale):
                for sx in range(scale):
                    px = x + (sx + 0.5) / scale
                    py = y + (sy + 0.5) / scale
                    inside = 0.0
                    if corner:
                        # rounded rectangle coverage
                        dx = max(abs(px - cx) - (size / 2 - corner), 0.0)
                        dy = max(abs(py - cy) - (size / 2 - corner), 0.0)
                        if dx * dx + dy * dy <= corner * corner:
                            inside = 1.0
                    else:
                        inside = 1.0
                    if inside == 0.0:
                        c = TRANSPARENT
                    else:
                        d = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
                        c = BRAND + (255,)
                        if abs(d - radius) <= ring_w / 2:
                            c = WHITE + (255,)
                        elif d <= dot_r:
                            c = WHITE + (255,)
                    a = c[3] / 255.0
                    for i in range(3):
                        acc[i] += c[i] * a
                    acc[3] += a * 255
            n = scale * scale
            if acc[3] <= 0:
                row += bytes((0, 0, 0, 0))
            else:
                alpha = acc[3] / n
                # un-premultiply so semi-transparent edge pixels keep the brand colour
                rgb = [min(255, round(acc[i] / n / (alpha / 255))) for i in range(3)]
                row += bytes((*rgb, min(255, round(alpha))))
        rows.append(bytes(row))

    raw = b"".join(b"\x00" + r for r in rows)
    return _png(size, size, raw)


def _png(width: int, height: int, raw: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-512.png", 512, True),
        ("apple-touch-icon.png", 180, False),
    ]
    for name, size, maskable in targets:
        data = render(size, maskable=maskable)
        (OUT / name).write_bytes(data)
        print(f"wrote docs/assets/{name} ({len(data)} bytes, {size}x{size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
