"""Temporary test strategy — not part of world mechanics."""

from __future__ import annotations

import random
from dataclasses import dataclass

from agentiki.sim.actions import (
    AgentAction,
    EatAction,
    InteractAction,
    MoveAction,
    MoveDirection,
    MOVE_DIRECTIONS,
)
from agentiki.sim.config import SimulationConfig
from agentiki.sim.foraging import (
    direction_toward,
    pick_eatable_food,
    pick_nearest_food,
)
from agentiki.sim.meetings import ContinueChoice, Meeting, MeetingStrategy
from agentiki.sim.pd import PDRoundResult, PDChoice
from agentiki.sim.perception import Observation, is_interactable


@dataclass
class RandomTestStrategy(MeetingStrategy):
    """Innate food-seeking + optional PD interact + random walk.

    Eating is a dedicated tick: only when food is already within
    ``interaction_radius`` the agent chooses ``EatAction`` and stays put.
    """

    interact_probability: float = 0.4
    continue_probability: float = 0.5

    def choose(
        self,
        observation: Observation,
        config: SimulationConfig,
        rng: random.Random,
    ) -> AgentAction:
        eatable = pick_eatable_food(
            observation.visible_food, config.interaction_radius, rng
        )
        if eatable is not None:
            return EatAction(food_id=eatable.food_id)

        target = pick_nearest_food(observation.visible_food, rng)
        if target is not None:
            return MoveAction(
                direction=direction_toward(
                    target.relative_x, target.relative_y, rng
                )
            )

        if config.enable_pd:
            interactable = [
                visible
                for visible in observation.visible_agents
                if is_interactable(config, visible.relative_x, visible.relative_y)
            ]
            if interactable and rng.random() < self.interact_probability:
                chosen = rng.choice(interactable)
                return InteractAction(target_agent_id=chosen.agent_id)
        return MoveAction(direction=rng.choice(MOVE_DIRECTIONS))

    def choose_pd(
        self,
        meeting: Meeting,
        agent_id: int,
        config: SimulationConfig,
        rng: random.Random,
    ) -> PDChoice:
        return rng.choice([PDChoice.COOPERATE, PDChoice.DEFECT])

    def choose_continue(
        self,
        meeting: Meeting,
        agent_id: int,
        round_result: PDRoundResult,
        config: SimulationConfig,
        rng: random.Random,
    ) -> ContinueChoice:
        if rng.random() < self.continue_probability:
            return ContinueChoice.CONTINUE
        return ContinueChoice.LEAVE
