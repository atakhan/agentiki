"""Simulation-wide parameters."""

from __future__ import annotations

from dataclasses import dataclass

from agentiki.sim.pd import PayoffMatrix


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    vision_radius: int = 3
    interaction_radius: int = 1
    payoff_matrix: PayoffMatrix = PayoffMatrix()

    def __post_init__(self) -> None:
        if self.vision_radius < 0:
            raise ValueError("vision_radius must be >= 0")
        if self.interaction_radius < 0:
            raise ValueError("interaction_radius must be >= 0")
        if self.interaction_radius > self.vision_radius:
            raise ValueError("interaction_radius must be <= vision_radius")
