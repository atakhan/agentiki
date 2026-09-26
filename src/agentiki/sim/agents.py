"""Agent layer: one agent per grid cell, extensible for movement and genomes."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

from agentiki.sim.spatial_hash import SpatialHash

MAX_AGENTS = 100_000


class AgentState(Enum):
    FREE = "FREE"
    IN_MEETING = "IN_MEETING"


@dataclass(slots=True)
class Agent:
    """Single agent anchored to a grid cell.

    ``pos_x`` / ``pos_y`` are normalized offsets inside the cell (0..1).
    Movement and genomes can extend this model without changing the API shape.
    """

    id: int
    cell_x: int
    cell_y: int
    pos_x: float = 0.5
    pos_y: float = 0.5
    genome: bytes | None = None
    state: AgentState = AgentState.FREE
    meeting_id: int | None = None
    score: int = 0

    @property
    def world_x(self) -> float:
        return self.cell_x + self.pos_x

    @property
    def world_y(self) -> float:
        return self.cell_y + self.pos_y


@dataclass
class AgentPopulation:
    """Occupancy map + spatial index for agent queries."""

    _agents: dict[int, Agent] = field(default_factory=dict)
    _occupancy: dict[tuple[int, int], int] = field(default_factory=dict)
    _next_id: int = 1
    spatial: SpatialHash = field(default_factory=lambda: SpatialHash(1.0))

    def clear(self) -> None:
        self._agents.clear()
        self._occupancy.clear()
        self._next_id = 1
        self.spatial.clear()

    def __len__(self) -> int:
        return len(self._agents)

    def list(self) -> list[Agent]:
        return list(self._agents.values())

    def get(self, agent_id: int) -> Agent | None:
        return self._agents.get(agent_id)

    def at_cell(self, cell_x: int, cell_y: int) -> Agent | None:
        agent_id = self._occupancy.get((cell_x, cell_y))
        if agent_id is None:
            return None
        return self._agents.get(agent_id)

    def iter_in_bounds(
        self,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
    ) -> Iterator[Agent]:
        for agent in self._agents.values():
            if min_x <= agent.cell_x <= max_x and min_y <= agent.cell_y <= max_y:
                yield agent

    def place(self, agent: Agent) -> None:
        """Insert a single agent (used by generation and tests)."""
        self._add(agent)

    def _add(self, agent: Agent) -> None:
        key = (agent.cell_x, agent.cell_y)
        if key in self._occupancy:
            raise ValueError(f"cell ({agent.cell_x}, {agent.cell_y}) already occupied")
        self._agents[agent.id] = agent
        self._occupancy[key] = agent.id
        self.spatial.insert(agent.id, agent.world_x, agent.world_y)

    def apply_positions(self, positions: dict[int, tuple[int, int]]) -> None:
        """Apply resolved positions in one atomic update."""
        self._occupancy.clear()
        self.spatial.clear()
        for agent_id, (cell_x, cell_y) in positions.items():
            agent = self._agents[agent_id]
            agent.cell_x = cell_x
            agent.cell_y = cell_y
            agent.pos_x = 0.5
            agent.pos_y = 0.5
            self._occupancy[(cell_x, cell_y)] = agent_id
            self.spatial.insert(agent_id, agent.world_x, agent.world_y)

    def generate(
        self,
        count: int,
        density: float,
        seed: int,
        origin_x: int = 0,
        origin_y: int = 0,
    ) -> list[Agent]:
        if count < 1:
            raise ValueError("count must be >= 1")
        if count > MAX_AGENTS:
            raise ValueError(f"count must be <= {MAX_AGENTS}")
        density = max(0.01, min(density, 10.0))

        self.clear()
        rng = random.Random(seed)

        radius = max(1, math.ceil(math.sqrt(count / (math.pi * density))))
        cells: list[tuple[int, int]] = []
        while len(cells) < count:
            cells = []
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        cells.append((origin_x + dx, origin_y + dy))
            if len(cells) < count:
                radius += 1
            else:
                break

        weights = [
            math.exp(-math.hypot(cx - origin_x, cy - origin_y) * density)
            for cx, cy in cells
        ]

        selected: list[tuple[int, int]] = []
        pool = list(cells)
        pool_weights = list(weights)
        target = min(count, len(pool))
        for _ in range(target):
            idx = rng.choices(range(len(pool)), weights=pool_weights, k=1)[0]
            selected.append(pool.pop(idx))
            pool_weights.pop(idx)

        created: list[Agent] = []
        for cell_x, cell_y in selected:
            agent = Agent(id=self._next_id, cell_x=cell_x, cell_y=cell_y)
            self._next_id += 1
            self._add(agent)
            created.append(agent)
        return created
