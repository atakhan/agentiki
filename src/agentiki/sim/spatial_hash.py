"""Uniform-grid spatial hash for nearby-agent queries (O(k) vs all-pairs)."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Hashable, Iterator


class SpatialHash:
    def __init__(self, cell_size: float = 4.0) -> None:
        if cell_size <= 0:
            raise ValueError("cell_size must be positive")
        self.cell_size = cell_size
        self._buckets: dict[tuple[int, int], list[tuple[Hashable, float, float]]] = (
            defaultdict(list)
        )

    def clear(self) -> None:
        self._buckets.clear()

    def _key(self, x: float, y: float) -> tuple[int, int]:
        return (math.floor(x / self.cell_size), math.floor(y / self.cell_size))

    def insert(self, entity_id: Hashable, x: float, y: float) -> None:
        self._buckets[self._key(x, y)].append((entity_id, x, y))

    def query_radius(
        self, x: float, y: float, radius: float
    ) -> Iterator[tuple[Hashable, float, float]]:
        if radius < 0:
            raise ValueError("radius must be non-negative")
        r2 = radius * radius
        min_i = math.floor((x - radius) / self.cell_size)
        max_i = math.floor((x + radius) / self.cell_size)
        min_j = math.floor((y - radius) / self.cell_size)
        max_j = math.floor((y + radius) / self.cell_size)
        buckets = self._buckets
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                for item in buckets.get((i, j), ()):
                    _eid, ex, ey = item
                    dx = ex - x
                    dy = ey - y
                    if dx * dx + dy * dy <= r2:
                        yield item

    def query_chebyshev(
        self,
        cell_x: int,
        cell_y: int,
        radius: int,
    ) -> Iterator[tuple[Hashable, float, float]]:
        """Entities in the Chebyshev square around a grid cell."""
        if radius < 0:
            raise ValueError("radius must be non-negative")
        min_i = cell_x - radius
        max_i = cell_x + radius
        min_j = cell_y - radius
        max_j = cell_y + radius
        buckets = self._buckets
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                yield from buckets.get((i, j), ())
