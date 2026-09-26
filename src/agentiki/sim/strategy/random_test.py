"""Temporary test strategy — not part of world mechanics."""

from __future__ import annotations

import random
from dataclasses import dataclass

from agentiki.sim.actions import (
    AgentAction,
    InteractAction,
    MoveAction,
    MoveDirection,
    MOVE_DIRECTIONS,
)
from agentiki.sim.config import SimulationConfig
from agentiki.sim.meetings import ContinueChoice, Meeting, MeetingStrategy
from agentiki.sim.pd import PDRoundResult, PDChoice
from agentiki.sim.perception import Observation, is_interactable


@dataclass
class RandomTestStrategy(MeetingStrategy):
    """Temporary test strategy — not part of world mechanics."""

    interact_probability: float = 0.4
    continue_probability: float = 0.5

    def choose(
        self,
        observation: Observation,
        config: SimulationConfig,
        rng: random.Random,
    ) -> AgentAction:
        interactable = [
            visible
            for visible in observation.visible_agents
            if is_interactable(config, visible.relative_x, visible.relative_y)
        ]
        if interactable and rng.random() < self.interact_probability:
            target = rng.choice(interactable)
            return InteractAction(target_agent_id=target.agent_id)
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
