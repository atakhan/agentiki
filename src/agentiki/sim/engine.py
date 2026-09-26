"""Deterministic tick loop + factory for sim backends (python now, rust later)."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from agentiki.sim.agents import Agent, AgentPopulation
from agentiki.sim.config import SimulationConfig
from agentiki.sim.interactions import Interaction
from agentiki.sim.meetings import MeetingStore
from agentiki.sim.results import StepResult
from agentiki.sim.movement import tick_rng
from agentiki.sim.perception import Observation, observe
from agentiki.sim.protocol import Cell, SimulationEngine
from agentiki.sim.spatial_hash import SpatialHash
from agentiki.sim.strategy import RandomTestStrategy
from agentiki.sim.tick import step_tick
from agentiki.sim.world import InfiniteWorld

DEFAULT_SPATIAL_CELL_SIZE = 4.0


class PythonEngine:
    backend = "python"

    def __init__(
        self,
        seed: int = 1,
        spatial_cell_size: float = DEFAULT_SPATIAL_CELL_SIZE,
        config: SimulationConfig | None = None,
    ) -> None:
        self._seed = seed
        self._tick = 0
        self._spatial_cell_size = spatial_cell_size
        self._config = config or SimulationConfig()
        self._world = InfiniteWorld(seed)
        self.spatial = SpatialHash(spatial_cell_size)
        self._agents = AgentPopulation()
        self._generation = 0
        self._strategy = RandomTestStrategy()
        self._meetings = MeetingStore()
        self._last_step_result: StepResult | None = None

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def tick(self) -> int:
        return self._tick

    @property
    def spatial_cell_size(self) -> float:
        return self._spatial_cell_size

    @property
    def config(self) -> SimulationConfig:
        return self._config

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    @property
    def last_step_result(self) -> StepResult | None:
        return self._last_step_result

    @property
    def last_interactions(self) -> Sequence[Interaction]:
        if self._last_step_result is None:
            return ()
        return self._last_step_result.interactions

    def step(self, n: int = 1) -> StepResult:
        if n < 0:
            raise ValueError("n must be >= 0")
        accumulated = StepResult(tick=self._tick, interactions=())
        for _ in range(n):
            if len(self._agents) > 0:
                rng = tick_rng(self._seed, self._tick)
                result = step_tick(
                    self._agents,
                    self._config,
                    self._strategy,
                    self._tick,
                    rng,
                    self._meetings,
                )
                accumulated = StepResult(
                    tick=result.tick + 1,
                    interactions=accumulated.interactions + result.interactions,
                    meetings_started=accumulated.meetings_started + result.meetings_started,
                    pd_rounds=accumulated.pd_rounds + result.pd_rounds,
                    meeting_outcomes=accumulated.meeting_outcomes + result.meeting_outcomes,
                )
            else:
                accumulated = StepResult(
                    tick=accumulated.tick + 1,
                    interactions=accumulated.interactions,
                    meetings_started=accumulated.meetings_started,
                    pd_rounds=accumulated.pd_rounds,
                    meeting_outcomes=accumulated.meeting_outcomes,
                )
            self._tick += 1
        self._last_step_result = accumulated
        return accumulated

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self._seed = seed
        self._tick = 0
        self._generation = 0
        self._last_step_result = None
        self._world = InfiniteWorld(self._seed)
        self.spatial.clear()
        self._agents.clear()
        self._meetings.clear()

    def cell(self, x: int, y: int) -> Cell:
        return self._world.cell(x, y)

    def iter_cells(
        self,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
        step: int = 1,
    ) -> Iterator[Cell]:
        return self._world.iter_cells(min_x, min_y, max_x, max_y, step)

    def list_agents(self) -> Sequence[Agent]:
        return self._agents.list()

    def agents_in_bounds(
        self,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
    ) -> Sequence[Agent]:
        return list(self._agents.iter_in_bounds(min_x, min_y, max_x, max_y))

    def generate_agents(
        self,
        count: int,
        density: float,
        *,
        origin_x: int = 0,
        origin_y: int = 0,
    ) -> Sequence[Agent]:
        gen_seed = self._seed ^ (self._generation * 0x9E3779B9) ^ (self._tick << 16)
        self._generation += 1
        return self._agents.generate(
            count=count,
            density=density,
            seed=gen_seed & 0xFFFFFFFF,
            origin_x=origin_x,
            origin_y=origin_y,
        )

    def observe(self, agent_id: int) -> Observation:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise ValueError(f"unknown agent_id: {agent_id}")
        return observe(agent, self._agents, self._config)


def create_engine(
    *,
    backend: str = "python",
    seed: int = 1,
    spatial_cell_size: float = DEFAULT_SPATIAL_CELL_SIZE,
    config: SimulationConfig | None = None,
) -> SimulationEngine:
    if backend == "python":
        return PythonEngine(seed=seed, spatial_cell_size=spatial_cell_size, config=config)
    if backend == "rust":
        return _load_rust_engine(
            seed=seed,
            spatial_cell_size=spatial_cell_size,
            config=config,
        )
    raise ValueError(f"unknown simulation backend: {backend!r}")


def _load_rust_engine(
    *,
    seed: int,
    spatial_cell_size: float,
    config: SimulationConfig | None,
) -> SimulationEngine:
    try:
        import agentiki_sim_rust  # type: ignore[import-not-found]
    except ImportError as exc:
        raise NotImplementedError(
            "Rust simulation core is not installed. Keep SimulationEngine stable "
            "and expose a pyo3 module named agentiki_sim_rust, or use "
            "AGENTIKI_SIM_BACKEND=python."
        ) from exc
    return agentiki_sim_rust.Engine(
        seed=seed,
        spatial_cell_size=spatial_cell_size,
        config=config,
    )
