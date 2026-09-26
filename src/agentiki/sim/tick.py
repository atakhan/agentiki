"""One simulation tick: observe → decide → resolve → apply."""

from __future__ import annotations

import random
from typing import Protocol

from agentiki.sim.actions import AgentAction, InteractAction, MoveAction, MoveDirection
from agentiki.sim.agents import AgentPopulation, AgentState
from agentiki.sim.config import SimulationConfig
from agentiki.sim.interactions import resolve_interactions
from agentiki.sim.results import StepResult
from agentiki.sim.meetings import (
    Meeting,
    MeetingStore,
    create_meetings_from_interactions,
    process_meeting_rounds,
)
from agentiki.sim.movement import build_intents_from_actions, resolve_moves
from agentiki.sim.pd import PDRoundResult
from agentiki.sim.perception import Observation, observe


class AgentStrategy(Protocol):
    def choose(
        self,
        observation: Observation,
        config: SimulationConfig,
        rng: random.Random,
    ) -> AgentAction: ...


def step_tick(
    population: AgentPopulation,
    config: SimulationConfig,
    strategy: AgentStrategy,
    tick: int,
    rng: random.Random,
    meeting_store: MeetingStore,
) -> StepResult:
    agents = {agent.id: (agent.cell_x, agent.cell_y) for agent in population.list()}
    continuing_meetings = tuple(
        sorted(meeting_store.active_meetings(), key=lambda item: item.meeting_id)
    )

    actions: dict[int, AgentAction] = {}
    for agent in sorted(population.list(), key=lambda item: item.id):
        if agent.state is not AgentState.FREE:
            continue
        observation = observe(agent, population, config)
        actions[agent.id] = strategy.choose(observation, config, rng)

    interact_intents: dict[int, int] = {}
    move_actions: dict[int, MoveDirection] = {
        agent.id: MoveDirection.STAY for agent in population.list()
    }
    for agent_id, action in actions.items():
        if isinstance(action, InteractAction):
            interact_intents[agent_id] = action.target_agent_id
        elif isinstance(action, MoveAction):
            move_actions[agent_id] = action.direction
        else:
            raise TypeError(f"unknown action type: {type(action)!r}")

    interactions = resolve_interactions(
        interact_intents,
        population,
        config,
        tick,
        busy_agents=meeting_store.busy_agents(),
    )

    meetings_started = create_meetings_from_interactions(
        interactions, meeting_store, population, tick
    )

    intents = build_intents_from_actions(agents, move_actions)
    final = resolve_moves(population._occupancy, intents)
    population.apply_positions(final)

    continuing_outcomes = process_meeting_rounds(
        continuing_meetings,
        meeting_store,
        population,
        config.payoff_matrix,
        strategy,
        config,
        rng,
        tick,
    )
    new_outcomes = process_meeting_rounds(
        meetings_started,
        meeting_store,
        population,
        config.payoff_matrix,
        strategy,
        config,
        rng,
        tick,
    )
    all_outcomes = continuing_outcomes + new_outcomes
    pd_rounds: tuple[PDRoundResult, ...] = tuple(
        outcome.round_result for outcome in all_outcomes
    )

    return StepResult(
        tick=tick,
        interactions=interactions,
        meetings_started=meetings_started,
        pd_rounds=pd_rounds,
        meeting_outcomes=all_outcomes,
    )
