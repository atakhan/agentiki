"""Simulation-wide parameters."""

from __future__ import annotations

from dataclasses import dataclass

from agentiki.sim.agents import (
    ENERGY_GAME,
    ENERGY_MOVE,
    ENERGY_PLAY_DECISION,
    ENERGY_STAY,
    HP_TICK,
    START_ENERGY,
    START_HP_MAX,
    START_HP_MIN,
)
from agentiki.sim.pd import PayoffMatrix
from agentiki.sim.world import DEFAULT_MAP_HEIGHT, DEFAULT_MAP_WIDTH


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    vision_radius: int = 3
    interaction_radius: int = 1
    map_width: int = DEFAULT_MAP_WIDTH
    map_height: int = DEFAULT_MAP_HEIGHT
    food_capacity: int = 50
    food_density_radius: int = 3
    food_energy: float = 10.0
    # PD / meetings stay in the codebase; off by default until re-enabled.
    enable_pd: bool = False
    start_hp_min: int = START_HP_MIN
    start_hp_max: int = START_HP_MAX
    hp_tick: int = HP_TICK
    start_energy: float = START_ENERGY
    energy_move: int = ENERGY_MOVE
    energy_stay: int = ENERGY_STAY
    energy_play_decision: int = ENERGY_PLAY_DECISION
    energy_game: int = ENERGY_GAME
    payoff_matrix: PayoffMatrix = PayoffMatrix()

    def __post_init__(self) -> None:
        if self.vision_radius < 0:
            raise ValueError("vision_radius must be >= 0")
        if self.interaction_radius < 0:
            raise ValueError("interaction_radius must be >= 0")
        if self.interaction_radius > self.vision_radius:
            raise ValueError("interaction_radius must be <= vision_radius")
        if self.map_width < 1:
            raise ValueError("map_width must be >= 1")
        if self.map_height < 1:
            raise ValueError("map_height must be >= 1")
        if self.food_capacity < 0:
            raise ValueError("food_capacity must be >= 0")
        if self.food_density_radius < 0:
            raise ValueError("food_density_radius must be >= 0")
        if self.food_energy < 0:
            raise ValueError("food_energy must be >= 0")
        if self.start_hp_min < 1:
            raise ValueError("start_hp_min must be >= 1")
        if self.start_hp_max < self.start_hp_min:
            raise ValueError("start_hp_max must be >= start_hp_min")
        if self.hp_tick < 0:
            raise ValueError("hp_tick must be >= 0")
        if self.start_energy < 0:
            raise ValueError("start_energy must be >= 0")
        for name in (
            "energy_move",
            "energy_stay",
            "energy_play_decision",
            "energy_game",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")

    def contains_cell(self, x: int, y: int) -> bool:
        return 0 <= x < self.map_width and 0 <= y < self.map_height
