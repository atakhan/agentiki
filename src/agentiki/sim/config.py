"""Simulation-wide parameters."""

from __future__ import annotations

from dataclasses import dataclass

from agentiki.sim.agents import HP_GAME, HP_MOVE, HP_PLAY_DECISION, HP_STAY, START_HP
from agentiki.sim.pd import PayoffMatrix


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    vision_radius: int = 3
    interaction_radius: int = 1
    start_hp: int = START_HP
    hp_move: int = HP_MOVE
    hp_stay: int = HP_STAY
    hp_play_decision: int = HP_PLAY_DECISION
    hp_game: int = HP_GAME
    payoff_matrix: PayoffMatrix = PayoffMatrix()

    def __post_init__(self) -> None:
        if self.vision_radius < 0:
            raise ValueError("vision_radius must be >= 0")
        if self.interaction_radius < 0:
            raise ValueError("interaction_radius must be >= 0")
        if self.interaction_radius > self.vision_radius:
            raise ValueError("interaction_radius must be <= vision_radius")
        if self.start_hp < 1:
            raise ValueError("start_hp must be >= 1")
        for name in ("hp_move", "hp_stay", "hp_play_decision", "hp_game"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")
