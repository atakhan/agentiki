"""Movement intents and simultaneous resolution."""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

from agentiki.sim.actions import MOVE_DIRECTIONS, MoveDirection

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


def resolve_moves(
    occupancy: dict[tuple[int, int], int],
    intents: dict[int, MoveIntent],
) -> dict[int, tuple[int, int]]:
    """Return final cell for every agent after simultaneous resolution."""
    move_intents: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {
        agent_id: (intent.from_cell, intent.target_cell) for agent_id, intent in intents.items()
    }

    dest_contenders: dict[tuple[int, int], list[int]] = defaultdict(list)
    for agent_id, (from_cell, to_cell) in move_intents.items():
        if to_cell != from_cell:
            dest_contenders[to_cell].append(agent_id)

    dest_winner: dict[tuple[int, int], int] = {
        dest: min(contenders) for dest, contenders in dest_contenders.items()
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
