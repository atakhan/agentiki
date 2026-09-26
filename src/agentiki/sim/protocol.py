"""Stable simulation-core contract.

The FastAPI layer talks only to ``SimulationEngine``. A future Rust/pyo3
backend can replace ``PythonEngine`` if it satisfies this protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Protocol, Sequence, runtime_checkable


@dataclass(frozen=True, slots=True)
class Cell:
    x: int
    y: int
    biome: str
    color: tuple[int, int, int]
    hash: int


@runtime_checkable
class SimulationEngine(Protocol):
    @property
    def backend(self) -> str: ...

    @property
    def seed(self) -> int: ...

    @property
    def tick(self) -> int: ...

    @property
    def spatial_cell_size(self) -> float: ...

    @property
    def agent_count(self) -> int: ...

    def step(self, n: int = 1): ...

    def reset(self, seed: int | None = None) -> None: ...

    def cell(self, x: int, y: int) -> Cell: ...

    def iter_cells(
        self,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
        step: int = 1,
    ) -> Iterator[Cell]: ...

    def list_agents(self) -> Sequence: ...

    def agents_in_bounds(
        self,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
    ) -> Sequence: ...

    def generate_agents(
        self,
        count: int,
        density: float,
        *,
        origin_x: int = 0,
        origin_y: int = 0,
    ) -> Sequence: ...

    @property
    def config(self): ...

    def observe(self, agent_id: int): ...

    @property
    def last_interactions(self) -> Sequence: ...
