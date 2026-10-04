from __future__ import annotations

from pydantic import BaseModel, Field


class WorldOut(BaseModel):
    backend: str
    seed: int
    tick: int
    spatial_cell_size: float
    default_cell_px: int = 50
    agent_count: int = 0
    vision_radius: int = 3
    interaction_radius: int = 1


class CellOut(BaseModel):
    x: int
    y: int
    biome: str
    color: str
    hash: int


class ResetIn(BaseModel):
    seed: int | None = None


class LifeRulesIn(BaseModel):
    """Life costs and PD incomes. Defaults match the engine constants."""

    start_hp: int = Field(default=60, ge=1)
    hp_move: int = Field(default=2, ge=0)
    hp_stay: int = Field(default=1, ge=0)
    hp_play_decision: int = Field(default=1, ge=0)
    hp_game: int = Field(default=1, ge=0)
    reward: int = Field(default=3, ge=0)
    temptation: int = Field(default=5, ge=0)
    punishment: int = Field(default=1, ge=0)
    sucker: int = Field(default=0, ge=0)


class WorldConfigIn(BaseModel):
    """Spawn settings for a named world. Not a running simulation."""

    name: str = Field(min_length=1, max_length=80)
    count: int = Field(default=100, ge=1, le=100_000)
    density: int = Field(default=1, ge=1, le=10)
    life: LifeRulesIn = Field(default_factory=LifeRulesIn)


class WorldConfigListOut(BaseModel):
    names: list[str]


class StepIn(BaseModel):
    n: int = Field(default=1, ge=0, le=10_000)
    life: LifeRulesIn = Field(default_factory=LifeRulesIn)


class AgentOut(BaseModel):
    id: int
    x: int
    y: int
    pos_x: float = 0.5
    pos_y: float = 0.5
    hp: int = 60
    state: str = "FREE"
    meeting_id: int | None = None


class AgentsOut(BaseModel):
    count: int
    agents: list[AgentOut]


class GenerateAgentsIn(BaseModel):
    count: int = Field(default=100, ge=1, le=100_000)
    density: float = Field(default=1.0, ge=1.0, le=10.0)
    origin_x: int = 0
    origin_y: int = 0
    life: LifeRulesIn = Field(default_factory=LifeRulesIn)


class InteractionOut(BaseModel):
    agent_a: int
    agent_b: int
    initiators: list[int]
    tick: int


class MeetingOut(BaseModel):
    meeting_id: int
    agent_a_id: int
    agent_b_id: int
    round_number: int
    status: str
    started_tick: int


class PDRoundOut(BaseModel):
    meeting_id: int
    agent_a_id: int
    agent_b_id: int
    round_number: int
    choice_a: str
    choice_b: str
    payoff_a: int
    payoff_b: int
    continue_a: str
    continue_b: str
    meeting_finished: bool
    tick: int


class StepOut(BaseModel):
    world: WorldOut
    agents: AgentsOut
    interactions: list[InteractionOut] = Field(default_factory=list)
    meetings_started: list[MeetingOut] = Field(default_factory=list)
    pd_rounds: list[PDRoundOut] = Field(default_factory=list)


class VisibleAgentOut(BaseModel):
    agent_id: int
    relative_x: int
    relative_y: int


class ObservationOut(BaseModel):
    observer_id: int
    vision_radius: int
    interaction_radius: int
    visible_agents: list[VisibleAgentOut]
