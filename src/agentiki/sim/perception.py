"""Local agent perception: observations from spatial queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agentiki.sim.config import SimulationConfig

if TYPE_CHECKING:
    from agentiki.sim.agents import Agent, AgentPopulation
    from agentiki.sim.food import FoodStore


@dataclass(frozen=True, slots=True)
class VisibleAgent:
    """Core representation; ``agent_id`` is for simulation internals, not strategy."""

    agent_id: int
    relative_x: int
    relative_y: int


@dataclass(frozen=True, slots=True)
class VisibleFood:
    """Food seen relative to the observer; ``food_id`` is for internals."""

    food_id: int
    relative_x: int
    relative_y: int


@dataclass(frozen=True, slots=True)
class RelativeAgent:
    """Strategy-facing view: relative position only."""

    relative_x: int
    relative_y: int


@dataclass(frozen=True, slots=True)
class RelativeFood:
    relative_x: int
    relative_y: int


@dataclass(frozen=True, slots=True)
class Observation:
    observer_id: int
    visible_agents: tuple[VisibleAgent, ...]
    visible_food: tuple[VisibleFood, ...] = ()

    def for_strategy(self) -> tuple[RelativeAgent, ...]:
        return tuple(
            RelativeAgent(v.relative_x, v.relative_y) for v in self.visible_agents
        )

    def food_for_strategy(self) -> tuple[RelativeFood, ...]:
        return tuple(
            RelativeFood(v.relative_x, v.relative_y) for v in self.visible_food
        )


def chebyshev_distance(dx: int, dy: int) -> int:
    return max(abs(dx), abs(dy))


def manhattan_distance(dx: int, dy: int) -> int:
    return abs(dx) + abs(dy)


def is_interactable(
    config: SimulationConfig,
    relative_x: int,
    relative_y: int,
) -> bool:
    distance = chebyshev_distance(relative_x, relative_y)
    return 0 < distance <= config.interaction_radius


def observe(
    observer: Agent,
    population: AgentPopulation,
    config: SimulationConfig,
    food_store: FoodStore | None = None,
) -> Observation:
    ox, oy = observer.cell_x, observer.cell_y
    visible: list[VisibleAgent] = []

    for other_id, _ex, _ey in population.spatial.query_chebyshev(
        ox, oy, config.vision_radius
    ):
        if other_id == observer.id:
            continue
        other = population.get(other_id)
        if other is None:
            continue
        rx = other.cell_x - ox
        ry = other.cell_y - oy
        if chebyshev_distance(rx, ry) <= config.vision_radius:
            visible.append(
                VisibleAgent(agent_id=other.id, relative_x=rx, relative_y=ry)
            )

    visible.sort(key=lambda item: item.agent_id)

    visible_food: list[VisibleFood] = []
    if food_store is not None:
        for food in food_store.list():
            rx = food.cell_x - ox
            ry = food.cell_y - oy
            if chebyshev_distance(rx, ry) <= config.vision_radius:
                visible_food.append(
                    VisibleFood(food_id=food.id, relative_x=rx, relative_y=ry)
                )
        visible_food.sort(key=lambda item: item.food_id)

    return Observation(
        observer_id=observer.id,
        visible_agents=tuple(visible),
        visible_food=tuple(visible_food),
    )
