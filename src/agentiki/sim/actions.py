"""Agent actions: movement and interaction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MoveDirection(Enum):
    STAY = "STAY"
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"


MOVE_DIRECTIONS: tuple[MoveDirection, ...] = (
    MoveDirection.STAY,
    MoveDirection.NORTH,
    MoveDirection.SOUTH,
    MoveDirection.EAST,
    MoveDirection.WEST,
)


@dataclass(frozen=True, slots=True)
class MoveAction:
    direction: MoveDirection


@dataclass(frozen=True, slots=True)
class InteractAction:
    target_agent_id: int


@dataclass(frozen=True, slots=True)
class EatAction:
    """Spend this tick eating a reachable food item (no movement)."""

    food_id: int


AgentAction = MoveAction | InteractAction | EatAction
