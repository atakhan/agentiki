"""Fixed rectangular seed-deterministic 2D cell field."""

from __future__ import annotations

from collections.abc import Iterator

from agentiki.sim.hashing import cell_biome, cell_color, cell_hash
from agentiki.sim.protocol import Cell

DEFAULT_MAP_WIDTH = 64
DEFAULT_MAP_HEIGHT = 64


class BoundedWorld:
    """Cells in ``[0, width) × [0, height)``; hash still seed-deterministic."""

    def __init__(
        self,
        seed: int,
        width: int = DEFAULT_MAP_WIDTH,
        height: int = DEFAULT_MAP_HEIGHT,
    ) -> None:
        if width < 1:
            raise ValueError("map width must be >= 1")
        if height < 1:
            raise ValueError("map height must be >= 1")
        self.seed = seed
        self.width = width
        self.height = height

    def contains(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def cell(self, x: int, y: int) -> Cell:
        if not self.contains(x, y):
            raise ValueError(
                f"cell ({x}, {y}) outside map [0, {self.width}) × [0, {self.height})"
            )
        seed = self.seed
        return Cell(
            x=x,
            y=y,
            biome=cell_biome(x, y, seed),
            color=cell_color(x, y, seed),
            hash=cell_hash(x, y, seed),
        )

    def iter_cells(
        self,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
        step: int = 1,
    ) -> Iterator[Cell]:
        if step < 1:
            raise ValueError("step must be >= 1")
        lo_x = max(min_x, 0)
        lo_y = max(min_y, 0)
        hi_x = min(max_x, self.width - 1)
        hi_y = min(max_y, self.height - 1)
        if hi_x < lo_x or hi_y < lo_y:
            return
        for y in range(lo_y, hi_y + 1, step):
            for x in range(lo_x, hi_x + 1, step):
                yield self.cell(x, y)


# Backward-compatible alias while callers migrate.
InfiniteWorld = BoundedWorld
