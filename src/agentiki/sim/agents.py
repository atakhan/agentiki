"""Agent layer: one agent per grid cell, extensible for movement and genomes."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

from agentiki.sim.genetics import Genome
from agentiki.sim.spatial_hash import SpatialHash

MAX_AGENTS = 100_000
START_HP = 60
START_HP_MIN = 40
START_HP_MAX = 80
HP_TICK = 1
ENERGY_MOVE = 2
ENERGY_STAY = 1
ENERGY_PLAY_DECISION = 1
ENERGY_GAME = 1
START_ENERGY = 100.0


class AgentState(Enum):
    FREE = "FREE"
    IN_MEETING = "IN_MEETING"


@dataclass(slots=True)
class Agent:
    """Single agent anchored to a grid cell.

    ``pos_x`` / ``pos_y`` are normalized offsets inside the cell (0..1).
    Movement can extend this model without changing the API shape.
    ``genome`` holds the three genetic scales when set. The tick does not
    read or edit it; spawning does not assign one.
    """

    id: int
    cell_x: int
    cell_y: int
    pos_x: float = 0.5
    pos_y: float = 0.5
    genome: Genome | None = None
    state: AgentState = AgentState.FREE
    meeting_id: int | None = None
    hp: int = START_HP
    energy: float = START_ENERGY

    @property
    def world_x(self) -> float:
        return self.cell_x + self.pos_x

    @property
    def world_y(self) -> float:
        return self.cell_y + self.pos_y


def spend_hp(agent: Agent, amount: int) -> None:
    agent.hp = max(0, agent.hp - amount)


def spend_energy(agent: Agent, amount: float) -> None:
    agent.energy = max(0.0, float(agent.energy) - float(amount))


def gain_energy(agent: Agent, amount: float) -> None:
    agent.energy = float(agent.energy) + float(amount)


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

    def remove(self, agent_id: int) -> None:
        """Drop an agent and rebuild occupancy. Used when hp reaches 0."""
        agent = self._agents.pop(agent_id, None)
        if agent is None:
            return
        self._occupancy.pop((agent.cell_x, agent.cell_y), None)
        self.spatial.clear()
        for remaining in self._agents.values():
            self.spatial.insert(remaining.id, remaining.world_x, remaining.world_y)

    def generate(
        self,
        count: int,
        density: float,
        seed: int,
        origin_x: int = 0,
        origin_y: int = 0,
        start_hp_min: int = START_HP_MIN,
        start_hp_max: int = START_HP_MAX,
        start_energy: float = START_ENERGY,
        hp_rng: random.Random | None = None,
        map_width: int | None = None,
        map_height: int | None = None,
    ) -> list[Agent]:
        """Place agents on a square lattice centered at ``(origin_x, origin_y)``.

        ``density`` is the spacing in cells to the nearest neighbor
        (axis-aligned distance). Placement is uniform and deterministic;
        ``seed`` is kept for API compatibility and does not affect positions.
        Starting hp is drawn uniformly from ``[start_hp_min, start_hp_max]``.

        When ``map_width`` / ``map_height`` are set, every cell must lie in
        ``[0, width) × [0, height)`` and ``count`` must not exceed map area.
        """
        del seed
        if count < 1:
            raise ValueError("count must be >= 1")
        if start_hp_min < 1:
            raise ValueError("start_hp_min must be >= 1")
        if start_hp_max < start_hp_min:
            raise ValueError("start_hp_max must be >= start_hp_min")
        if start_energy < 0:
            raise ValueError("start_energy must be >= 0")
        if count > MAX_AGENTS:
            raise ValueError(f"count must be <= {MAX_AGENTS}")
        if map_width is not None and map_height is not None:
            if map_width < 1 or map_height < 1:
                raise ValueError("map dimensions must be >= 1")
            if count > map_width * map_height:
                raise ValueError(
                    f"count {count} exceeds map capacity {map_width * map_height}"
                )
        spacing = max(1, min(10, int(round(density))))
        rng = hp_rng if hp_rng is not None else random.Random(0)

        self.clear()

        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        x0 = origin_x - ((cols - 1) * spacing) // 2
        y0 = origin_y - ((rows - 1) * spacing) // 2

        created: list[Agent] = []
        for index in range(count):
            col = index % cols
            row = index // cols
            cell_x = x0 + col * spacing
            cell_y = y0 + row * spacing
            if map_width is not None and map_height is not None:
                if not (0 <= cell_x < map_width and 0 <= cell_y < map_height):
                    raise ValueError(
                        f"placement does not fit map {map_width}×{map_height} "
                        f"with count={count} density={spacing}"
                    )
            agent = Agent(
                id=self._next_id,
                cell_x=cell_x,
                cell_y=cell_y,
                hp=rng.randint(start_hp_min, start_hp_max),
                energy=float(start_energy),
            )
            self._next_id += 1
            self._add(agent)
            created.append(agent)
        return created
