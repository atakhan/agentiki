"""Deterministic u32 hashing shared conceptually with the TypeScript renderer."""

from __future__ import annotations

MASK32 = 0xFFFFFFFF

CELL_RGB: tuple[int, int, int] = (232, 234, 237)


def u32(n: int) -> int:
    return n & MASK32


def mix32(h: int) -> int:
    h = u32(h)
    h = u32(h ^ (h >> 16))
    h = u32(h * 0x7FEB352D)
    h = u32(h ^ (h >> 15))
    h = u32(h * 0x846CA68B)
    h = u32(h ^ (h >> 16))
    return h


def cell_hash(x: int, y: int, seed: int) -> int:
    h = u32(seed)
    h = u32(h + u32(u32(x) * 0x9E3779B1))
    h = u32(h ^ u32(y))
    h = u32(h + u32(u32(y) * 0x85EBCA77))
    return mix32(h)


def cell_biome(_x: int, _y: int, _seed: int) -> str:
    return "cell"


def cell_color(_x: int, _y: int, _seed: int) -> tuple[int, int, int]:
    return CELL_RGB
