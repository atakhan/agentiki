"""One simulation tick: observe → decide → resolve → apply."""

from __future__ import annotations

import random
from typing import Protocol

from agentiki.sim.actions import (
    AgentAction,
    EatAction,
    InteractAction,
    MoveAction,
    MoveDirection,
)
from agentiki.sim.agents import (
    AgentPopulation,
    AgentState,
    spend_energy,
    spend_hp,
)
from agentiki.sim.config import SimulationConfig
from agentiki.sim.food import FoodStore, process_food_consumption
from agentiki.sim.foraging import pick_eatable_food
from agentiki.sim.interactions import resolve_interactions
from agentiki.sim.results import StepResult
from agentiki.sim.meetings import (
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
    *,
    seed: int = 1,
    food_store: FoodStore | None = None,
) -> StepResult:
    agents = {agent.id: (agent.cell_x, agent.cell_y) for agent in population.list()}
    continuing_meetings = tuple(
        sorted(meeting_store.active_meetings(), key=lambda item: item.meeting_id)
    )

    actions: dict[int, AgentAction] = {}
    for agent in sorted(population.list(), key=lambda item: item.id):
        observation = observe(agent, population, config, food_store)
        if agent.state is AgentState.IN_MEETING:
            # Meetings block movement/interact, but eating remains allowed.
            eatable = pick_eatable_food(
                observation.visible_food, config.interaction_radius, rng
            )
            if eatable is not None:
                actions[agent.id] = EatAction(food_id=eatable.food_id)
            continue
        if agent.state is not AgentState.FREE:
            continue
        actions[agent.id] = strategy.choose(observation, config, rng)

    if not config.enable_pd:
        # Keep InteractAction in the type system, but do not start PD while disabled.
        for agent_id, action in list(actions.items()):
            if isinstance(action, InteractAction):
                actions[agent_id] = MoveAction(direction=MoveDirection.STAY)

    interact_intents: dict[int, int] = {}
    eat_intents: dict[int, int] = {}
    move_actions: dict[int, MoveDirection] = {
        agent.id: MoveDirection.STAY for agent in population.list()
    }
    for agent_id, action in actions.items():
        if isinstance(action, InteractAction):
            interact_intents[agent_id] = action.target_agent_id
        elif isinstance(action, EatAction):
            eat_intents[agent_id] = action.food_id
            move_actions[agent_id] = MoveDirection.STAY
        elif isinstance(action, MoveAction):
            move_actions[agent_id] = action.direction
        else:
            raise TypeError(f"unknown action type: {type(action)!r}")

    if config.enable_pd:
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
    else:
        interactions = ()
        meetings_started = ()

    intents = build_intents_from_actions(agents, move_actions)
    final = resolve_moves(
        population._occupancy,
        intents,
        seed=seed,
        tick=tick,
        map_width=config.map_width,
        map_height=config.map_height,
    )
    population.apply_positions(final)

    for agent in population.list():
        start = agents[agent.id]
        moved = (agent.cell_x, agent.cell_y) != start
        spend_energy(
            agent, config.energy_move if moved else config.energy_stay
        )
        if isinstance(actions.get(agent.id), InteractAction):
            spend_energy(agent, config.energy_play_decision)

    food_consumed: tuple = ()
    food_spawned: tuple = ()
    if food_store is not None:
        food_consumed, food_spawned = process_food_consumption(
            food_store,
            population,
            config,
            tick,
            seed=seed,
            rng=rng,
            eat_intents=eat_intents,
        )

    if config.enable_pd:
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
    else:
        all_outcomes = ()
    pd_rounds: tuple[PDRoundResult, ...] = tuple(
        outcome.round_result for outcome in all_outcomes
    )

    # Life is a constant per-tick drain; never replenished.
    for agent in population.list():
        spend_hp(agent, config.hp_tick)

    # Death: life exhausted or energy depleted.
    for agent_id in [
        agent.id
        for agent in population.list()
        if agent.hp <= 0 or agent.energy <= 0
    ]:
        meeting_store.finish_for_agent(agent_id, population)
        population.remove(agent_id)

    return StepResult(
        tick=tick,
        interactions=interactions,
        meetings_started=meetings_started,
        pd_rounds=pd_rounds,
        meeting_outcomes=all_outcomes,
        food_consumed=food_consumed,
        food_spawned=food_spawned,
    )
