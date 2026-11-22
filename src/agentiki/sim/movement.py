"""Movement intents and simultaneous resolution."""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

from agentiki.sim.actions import MOVE_DIRECTIONS, MoveDirection
from agentiki.sim.hashing import mix32, u32

# Backward-compatible alias used by tests and movement intents.
Action = MoveDirection
ACTIONS = MOVE_DIRECTIONS


@dataclass(frozen=True, slots=True)
class MoveIntent:
    agent_id: int
    from_cell: tuple[int, int]
    action: MoveDirection
    target_cell: tuple[int, int]


def tick_rng(seed: int, tick: int) -> random.Random:
    return random.Random((seed ^ (tick * 0x9E3779B9)) & 0xFFFFFFFF)


def move_priority(
    seed: int,
    tick: int,
    dest_x: int,
    dest_y: int,
    agent_id: int,
) -> int:
    """Deterministic lottery key for a destination conflict.

    Higher value wins. Same (seed, tick, destination, agent_id) always yields
    the same priority, so runs are reproducible without fairness state.
    """
    h = u32(seed)
    h = u32(h + u32(tick * 0x9E3779B9))
    h = u32(h ^ u32(dest_x))
    h = u32(h + u32(u32(dest_x) * 0x9E3779B1))
    h = u32(h ^ u32(dest_y))
    h = u32(h + u32(u32(dest_y) * 0x85EBCA77))
    h = u32(h ^ u32(agent_id))
    h = u32(h + u32(u32(agent_id) * 0xC2B2AE3D))
    return mix32(h)


def target_cell(cell_x: int, cell_y: int, action: MoveDirection) -> tuple[int, int]:
    if action is MoveDirection.STAY:
        return (cell_x, cell_y)
    if action is MoveDirection.NORTH:
        return (cell_x, cell_y + 1)
    if action is MoveDirection.SOUTH:
        return (cell_x, cell_y - 1)
    if action is MoveDirection.EAST:
        return (cell_x + 1, cell_y)
    if action is MoveDirection.WEST:
        return (cell_x - 1, cell_y)
    raise ValueError(f"unknown action: {action!r}")


def build_intents_from_actions(
    agents: dict[int, tuple[int, int]],
    actions: dict[int, MoveDirection],
) -> dict[int, MoveIntent]:
    intents: dict[int, MoveIntent] = {}
    for agent_id in sorted(agents):
        from_cell = agents[agent_id]
        action = actions[agent_id]
        intents[agent_id] = MoveIntent(
            agent_id=agent_id,
            from_cell=from_cell,
            action=action,
            target_cell=target_cell(from_cell[0], from_cell[1], action),
        )
    return intents


def _pick_dest_winner(
    dest: tuple[int, int],
    contenders: list[int],
    *,
    seed: int,
    tick: int,
) -> int:
    dest_x, dest_y = dest
    return max(
        contenders,
        key=lambda agent_id: (
            move_priority(seed, tick, dest_x, dest_y, agent_id),
            agent_id,
        ),
    )


def resolve_moves(
    occupancy: dict[tuple[int, int], int],
    intents: dict[int, MoveIntent],
    *,
    seed: int = 1,
    tick: int = 0,
    map_width: int | None = None,
    map_height: int | None = None,
) -> dict[int, tuple[int, int]]:
    """Return final cell for every agent after simultaneous resolution.

    Targets outside ``[0, map_width) × [0, map_height)`` are treated as stay
    (hard walls). ``None`` bounds keep the previous unbounded behaviour for
    unit tests that only exercise conflict logic.
    """
    move_intents: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {}
    for agent_id, intent in intents.items():
        from_cell = intent.from_cell
        to_cell = intent.target_cell
        if map_width is not None and map_height is not None:
            tx, ty = to_cell
            if not (0 <= tx < map_width and 0 <= ty < map_height):
                to_cell = from_cell
        move_intents[agent_id] = (from_cell, to_cell)

    dest_contenders: dict[tuple[int, int], list[int]] = defaultdict(list)
    for agent_id, (from_cell, to_cell) in move_intents.items():
        if to_cell != from_cell:
            dest_contenders[to_cell].append(agent_id)

    dest_winner: dict[tuple[int, int], int] = {
        dest: _pick_dest_winner(dest, contenders, seed=seed, tick=tick)
        for dest, contenders in dest_contenders.items()
    }

    memo: dict[int, bool] = {}

    def can_succeed(agent_id: int, visiting: frozenset[int]) -> bool:
        if agent_id in memo:
            return memo[agent_id]
        if agent_id in visiting:
            memo[agent_id] = False
            return False

        from_cell, to_cell = move_intents[agent_id]
        if from_cell == to_cell:
            memo[agent_id] = True
            return True

        if dest_winner.get(to_cell) != agent_id:
            memo[agent_id] = False
            return False

        occupant_id = occupancy.get(to_cell)
        if occupant_id is None:
            memo[agent_id] = True
            return True
        if occupant_id == agent_id:
            memo[agent_id] = True
            return True

        occ_from, occ_to = move_intents[occupant_id]
        if occ_to == to_cell:
            memo[agent_id] = False
            return False

        next_visiting = visiting | {agent_id}
        if not can_succeed(occupant_id, next_visiting):
            memo[agent_id] = False
            return False

        memo[agent_id] = True
        return True

    final: dict[int, tuple[int, int]] = {}
    for agent_id, (from_cell, to_cell) in move_intents.items():
        if can_succeed(agent_id, frozenset()):
            final[agent_id] = to_cell
        else:
            final[agent_id] = from_cell
    return final
