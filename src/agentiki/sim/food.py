"""Food entities: occupancy, shared consumption, and density-based replenishment."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from agentiki.sim.agents import gain_energy
from agentiki.sim.movement import move_priority
from agentiki.sim.perception import chebyshev_distance

if TYPE_CHECKING:
    from agentiki.sim.agents import AgentPopulation
    from agentiki.sim.config import SimulationConfig


@dataclass(frozen=True, slots=True)
class Food:
    id: int
    cell_x: int
    cell_y: int
    energy: float


@dataclass(frozen=True, slots=True)
class FoodConsumption:
    """One agent's share from a (possibly shared) consumption event."""

    agent_id: int
    food_id: int
    cell_x: int
    cell_y: int
    energy: float
    tick: int
    consumer_count: int


@dataclass
class FoodStore:
    _by_id: dict[int, Food] = field(default_factory=dict)
    _occupancy: dict[tuple[int, int], int] = field(default_factory=dict)
    _next_id: int = 1

    def clear(self) -> None:
        self._by_id.clear()
        self._occupancy.clear()
        self._next_id = 1

    def __len__(self) -> int:
        return len(self._by_id)

    def list(self) -> list[Food]:
        return list(self._by_id.values())

    def get(self, food_id: int) -> Food | None:
        return self._by_id.get(food_id)

    def at_cell(self, cell_x: int, cell_y: int) -> Food | None:
        food_id = self._occupancy.get((cell_x, cell_y))
        if food_id is None:
            return None
        return self._by_id.get(food_id)

    def occupied_cells(self) -> set[tuple[int, int]]:
        return set(self._occupancy)

    def _add(self, food: Food) -> None:
        key = (food.cell_x, food.cell_y)
        if key in self._occupancy:
            raise ValueError(f"food cell ({food.cell_x}, {food.cell_y}) already occupied")
        self._by_id[food.id] = food
        self._occupancy[key] = food.id

    def remove(self, food_id: int) -> Food | None:
        food = self._by_id.pop(food_id, None)
        if food is None:
            return None
        self._occupancy.pop((food.cell_x, food.cell_y), None)
        return food

    def place(self, cell_x: int, cell_y: int, energy: float) -> Food:
        food = Food(
            id=self._next_id,
            cell_x=cell_x,
            cell_y=cell_y,
            energy=float(energy),
        )
        self._next_id += 1
        self._add(food)
        return food


def _chebyshev_count(
    center_x: int,
    center_y: int,
    radius: int,
    occupied: set[tuple[int, int]] | dict[tuple[int, int], object],
) -> int:
    total = 0
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if (center_x + dx, center_y + dy) in occupied:
                total += 1
    return total


def cell_density(
    cell_x: int,
    cell_y: int,
    radius: int,
    agent_cells: set[tuple[int, int]] | dict[tuple[int, int], object],
    food_cells: set[tuple[int, int]] | dict[tuple[int, int], object],
) -> int:
    return _chebyshev_count(cell_x, cell_y, radius, agent_cells) + _chebyshev_count(
        cell_x, cell_y, radius, food_cells
    )


def _free_cells(
    map_width: int,
    map_height: int,
    agent_cells: set[tuple[int, int]],
    food_cells: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    free: list[tuple[int, int]] = []
    for y in range(map_height):
        for x in range(map_width):
            key = (x, y)
            if key not in agent_cells and key not in food_cells:
                free.append(key)
    return free


def pick_lowest_density_cell(
    map_width: int,
    map_height: int,
    radius: int,
    agent_cells: set[tuple[int, int]],
    food_cells: set[tuple[int, int]],
    *,
    seed: int,
    tick: int,
) -> tuple[int, int] | None:
    candidates = _free_cells(map_width, map_height, agent_cells, food_cells)
    if not candidates:
        return None

    best_cell = candidates[0]
    best_density = cell_density(
        best_cell[0], best_cell[1], radius, agent_cells, food_cells
    )
    best_priority = move_priority(seed, tick, best_cell[0], best_cell[1], 0)

    for cell in candidates[1:]:
        density = cell_density(cell[0], cell[1], radius, agent_cells, food_cells)
        priority = move_priority(seed, tick, cell[0], cell[1], 0)
        if density < best_density or (
            density == best_density and priority > best_priority
        ):
            best_cell = cell
            best_density = density
            best_priority = priority
    return best_cell


def spawn_initial_food(
    store: FoodStore,
    population: AgentPopulation,
    config: SimulationConfig,
    rng: random.Random,
) -> list[Food]:
    """Place ``food_capacity`` units on empty cells; deterministic via ``rng``."""
    store.clear()
    capacity = config.food_capacity
    if capacity < 1:
        return []

    agent_cells = {(agent.cell_x, agent.cell_y) for agent in population.list()}
    free = _free_cells(
        config.map_width, config.map_height, agent_cells, set()
    )
    if len(free) < capacity:
        raise ValueError(
            f"cannot place {capacity} food: only {len(free)} free cells "
            f"on {config.map_width}×{config.map_height}"
        )

    chosen = rng.sample(free, capacity)
    created: list[Food] = []
    for cell_x, cell_y in chosen:
        created.append(store.place(cell_x, cell_y, config.food_energy))
    return created


def replenish_one(
    store: FoodStore,
    population: AgentPopulation,
    config: SimulationConfig,
    *,
    seed: int,
    tick: int,
) -> Food | None:
    agent_cells = {(agent.cell_x, agent.cell_y) for agent in population.list()}
    food_cells = store.occupied_cells()
    cell = pick_lowest_density_cell(
        config.map_width,
        config.map_height,
        config.food_density_radius,
        agent_cells,
        food_cells,
        seed=seed,
        tick=tick,
    )
    if cell is None:
        return None
    return store.place(cell[0], cell[1], config.food_energy)


def process_food_consumption(
    store: FoodStore,
    population: AgentPopulation,
    config: SimulationConfig,
    tick: int,
    *,
    seed: int,
    rng: random.Random,
    eat_intents: dict[int, int] | None = None,
) -> tuple[tuple[FoodConsumption, ...], tuple[Food, ...]]:
    """Batch shared consumption for agents that spent this tick eating.

    ``eat_intents`` maps agent_id → food_id from ``EatAction``. Agents must
    still be within ``interaction_radius`` after movement. Newly replenished
    food is not available for consumption in this call.
    """
    del rng  # reserved for future intent tie-breaks; intents already resolved
    if config.food_capacity < 1 or len(store) == 0:
        return (), ()
    if not eat_intents:
        return (), ()

    radius = config.interaction_radius

    # Validate intents: agent in range of the chosen food; one food per agent.
    agent_food: dict[int, int] = {}
    for agent_id, food_id in sorted(eat_intents.items()):
        agent = population.get(agent_id)
        food = store.get(food_id)
        if agent is None or food is None:
            continue
        dx = food.cell_x - agent.cell_x
        dy = food.cell_y - agent.cell_y
        if chebyshev_distance(dx, dy) > radius:
            continue
        agent_food[agent_id] = food_id

    # Group consumers by chosen food.
    groups: dict[int, list[int]] = {}
    for agent_id, food_id in agent_food.items():
        groups.setdefault(food_id, []).append(agent_id)

    events: list[FoodConsumption] = []
    consumed_ids: list[int] = []
    for food_id in sorted(groups):
        food = store.get(food_id)
        if food is None:
            continue
        consumers = sorted(groups[food_id])
        if not consumers:
            continue
        share = float(config.food_energy) / len(consumers)
        for agent_id in consumers:
            agent = population.get(agent_id)
            if agent is not None:
                gain_energy(agent, share)
            events.append(
                FoodConsumption(
                    agent_id=agent_id,
                    food_id=food_id,
                    cell_x=food.cell_x,
                    cell_y=food.cell_y,
                    energy=share,
                    tick=tick,
                    consumer_count=len(consumers),
                )
            )
        consumed_ids.append(food_id)

    for food_id in consumed_ids:
        store.remove(food_id)

    spawned: list[Food] = []
    for index, _food_id in enumerate(consumed_ids):
        placed = replenish_one(
            store,
            population,
            config,
            seed=seed,
            tick=tick + index,  # diversify placement ties within the same tick
        )
        if placed is not None:
            spawned.append(placed)

    return tuple(events), tuple(spawned)
