"""Innate food-seeking movement helpers (not genome/PD dependent)."""

from __future__ import annotations

import random

from agentiki.sim.actions import MoveDirection
from agentiki.sim.perception import (
    VisibleFood,
    chebyshev_distance,
    manhattan_distance,
)


def pick_nearest_food(
    visible_food: tuple[VisibleFood, ...] | list[VisibleFood],
    rng: random.Random,
) -> VisibleFood | None:
    if not visible_food:
        return None
    best = min(manhattan_distance(f.relative_x, f.relative_y) for f in visible_food)
    ties = [
        food
        for food in visible_food
        if manhattan_distance(food.relative_x, food.relative_y) == best
    ]
    return rng.choice(ties)


def pick_eatable_food(
    visible_food: tuple[VisibleFood, ...] | list[VisibleFood],
    interaction_radius: int,
    rng: random.Random,
) -> VisibleFood | None:
    """Food within Chebyshev ≤ interaction_radius (needs a dedicated Eat tick)."""
    eatable = [
        food
        for food in visible_food
        if chebyshev_distance(food.relative_x, food.relative_y) <= interaction_radius
    ]
    return pick_nearest_food(eatable, rng)


def direction_toward(
    relative_x: int,
    relative_y: int,
    rng: random.Random,
) -> MoveDirection:
    """One cardinal step that reduces Manhattan distance to the target."""
    options: list[MoveDirection] = []
    if relative_x > 0:
        options.append(MoveDirection.EAST)
    elif relative_x < 0:
        options.append(MoveDirection.WEST)
    if relative_y > 0:
        options.append(MoveDirection.NORTH)
    elif relative_y < 0:
        options.append(MoveDirection.SOUTH)
    if not options:
        return MoveDirection.STAY
    return rng.choice(options)
