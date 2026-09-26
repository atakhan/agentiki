"""Interaction events and simultaneous resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agentiki.sim.config import SimulationConfig
from agentiki.sim.perception import is_interactable

if TYPE_CHECKING:
    from agentiki.sim.agents import AgentPopulation


@dataclass(frozen=True, slots=True)
class Interaction:
    agent_a: int
    agent_b: int
    initiators: frozenset[int]
    tick: int


def is_valid_interact(
    initiator_id: int,
    target_id: int,
    population: AgentPopulation,
    config: SimulationConfig,
) -> bool:
    if initiator_id == target_id:
        return False
    initiator = population.get(initiator_id)
    target = population.get(target_id)
    if initiator is None or target is None:
        return False
    rx = target.cell_x - initiator.cell_x
    ry = target.cell_y - initiator.cell_y
    return is_interactable(config, rx, ry)


def resolve_interactions(
    interact_intents: dict[int, int],
    population: AgentPopulation,
    config: SimulationConfig,
    tick: int,
    *,
    busy_agents: set[int] | None = None,
) -> tuple[Interaction, ...]:
    unavailable = busy_agents or set()
    valid_edges = [
        (initiator, target)
        for initiator, target in sorted(interact_intents.items())
        if initiator not in unavailable
        and target not in unavailable
        and is_valid_interact(initiator, target, population, config)
    ]
    edge_set = set(valid_edges)
    used: set[int] = set()
    result: list[Interaction] = []
    processed_pairs: set[tuple[int, int]] = set()

    for a, b in valid_edges:
        if (b, a) not in edge_set:
            continue
        pair = (min(a, b), max(a, b))
        if pair in processed_pairs:
            continue
        if a in used or b in used:
            processed_pairs.add(pair)
            continue
        result.append(
            Interaction(
                agent_a=pair[0],
                agent_b=pair[1],
                initiators=frozenset({a, b}),
                tick=tick,
            )
        )
        used.add(a)
        used.add(b)
        processed_pairs.add(pair)

    for a, b in valid_edges:
        if a in used or b in used:
            continue
        if (b, a) in edge_set:
            continue
        pair = (min(a, b), max(a, b))
        result.append(
            Interaction(
                agent_a=pair[0],
                agent_b=pair[1],
                initiators=frozenset({a}),
                tick=tick,
            )
        )
        used.add(a)
        used.add(b)

    result.sort(key=lambda item: (item.agent_a, item.agent_b))
    return tuple(result)
