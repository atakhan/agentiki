"""Infinite, seed-deterministic 2D cell field."""

from __future__ import annotations

from collections.abc import Iterator

from agentiki.sim.hashing import cell_biome, cell_color, cell_hash
from agentiki.sim.protocol import Cell


class InfiniteWorld:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def cell(self, x: int, y: int) -> Cell:
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
        if max_x < min_x or max_y < min_y:
            return
        for y in range(min_y, max_y + 1, step):
            for x in range(min_x, max_x + 1, step):
                yield self.cell(x, y)
