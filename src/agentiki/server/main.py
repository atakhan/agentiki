from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agentiki.sim import create_engine
from agentiki.server.schemas import (
    AgentOut,
    AgentsOut,
    CellOut,
    GenerateAgentsIn,
    InteractionOut,
    MeetingOut,
    ObservationOut,
    PDRoundOut,
    ResetIn,
    StepIn,
    StepOut,
    VisibleAgentOut,
    WorldOut,
)

DEFAULT_CELL_PX = 50
MAX_VIEWPORT_CELLS = 20_000


def _engine(request: Request):
    return request.app.state.engine


def _agent_out(agent) -> AgentOut:
    return AgentOut(
        id=agent.id,
        x=agent.cell_x,
        y=agent.cell_y,
        pos_x=agent.pos_x,
        pos_y=agent.pos_y,
        score=agent.score,
        state=agent.state.value,
        meeting_id=agent.meeting_id,
    )


def _agents_out(agents) -> AgentsOut:
    items = [_agent_out(agent) for agent in agents]
    return AgentsOut(count=len(items), agents=items)


def _interaction_out(interaction) -> InteractionOut:
    return InteractionOut(
        agent_a=interaction.agent_a,
        agent_b=interaction.agent_b,
        initiators=sorted(interaction.initiators),
        tick=interaction.tick,
    )


def _meeting_out(meeting) -> MeetingOut:
    return MeetingOut(
        meeting_id=meeting.meeting_id,
        agent_a_id=meeting.agent_a_id,
        agent_b_id=meeting.agent_b_id,
        round_number=meeting.round_number,
        status=meeting.status.value,
        started_tick=meeting.started_tick,
    )


def _meeting_round_out(outcome) -> PDRoundOut:
    round_result = outcome.round_result
    return PDRoundOut(
        meeting_id=round_result.meeting_id,
        agent_a_id=round_result.agent_a_id,
        agent_b_id=round_result.agent_b_id,
        round_number=round_result.round_number,
        choice_a=round_result.choice_a.value,
        choice_b=round_result.choice_b.value,
        payoff_a=round_result.payoff_a,
        payoff_b=round_result.payoff_b,
        continue_a=outcome.continue_a.value,
        continue_b=outcome.continue_b.value,
        meeting_finished=outcome.meeting_finished,
        tick=round_result.tick,
    )


def _cell_out(cell) -> CellOut:
    r, g, b = cell.color
    return CellOut(
        x=cell.x,
        y=cell.y,
        biome=cell.biome,
        color=f"#{r:02x}{g:02x}{b:02x}",
        hash=cell.hash,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    backend = os.environ.get("AGENTIKI_SIM_BACKEND", "python")
    seed = int(os.environ.get("AGENTIKI_SEED", "1"))
    app.state.engine = create_engine(backend=backend, seed=seed)
    yield


app = FastAPI(title="agentiki", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/world", response_model=WorldOut)
def world(request: Request) -> WorldOut:
    engine = _engine(request)
    cfg = engine.config
    return WorldOut(
        backend=engine.backend,
        seed=engine.seed,
        tick=engine.tick,
        spatial_cell_size=engine.spatial_cell_size,
        default_cell_px=DEFAULT_CELL_PX,
        agent_count=engine.agent_count,
        vision_radius=cfg.vision_radius,
        interaction_radius=cfg.interaction_radius,
    )


@app.get("/api/world/cell", response_model=CellOut)
def world_cell(
    request: Request,
    x: int = Query(),
    y: int = Query(),
) -> CellOut:
    return _cell_out(_engine(request).cell(x, y))


@app.get("/api/world/cells", response_model=list[CellOut])
def world_cells(
    request: Request,
    min_x: int = Query(),
    min_y: int = Query(),
    max_x: int = Query(),
    max_y: int = Query(),
    step: int = Query(default=1, ge=1),
) -> list[CellOut]:
    width = (max_x - min_x) // step + 1
    height = (max_y - min_y) // step + 1
    if width <= 0 or height <= 0:
        return []
    if width * height > MAX_VIEWPORT_CELLS:
        raise HTTPException(
            status_code=400,
            detail=f"viewport too large ({width * height} cells, max {MAX_VIEWPORT_CELLS})",
        )
    return [_cell_out(cell) for cell in _engine(request).iter_cells(min_x, min_y, max_x, max_y, step)]


@app.post("/api/world/step", response_model=StepOut)
def world_step(request: Request, body: StepIn) -> StepOut:
    engine = _engine(request)
    result = engine.step(body.n)
    return StepOut(
        world=world(request),
        agents=_agents_out(engine.list_agents()),
        interactions=[_interaction_out(item) for item in result.interactions],
        meetings_started=[_meeting_out(item) for item in result.meetings_started],
        pd_rounds=[_meeting_round_out(item) for item in result.meeting_outcomes],
    )


@app.post("/api/world/reset", response_model=WorldOut)
def world_reset(request: Request, body: ResetIn) -> WorldOut:
    _engine(request).reset(body.seed)
    return world(request)


@app.get("/api/agents", response_model=AgentsOut)
def list_agents(
    request: Request,
    min_x: int | None = Query(default=None),
    min_y: int | None = Query(default=None),
    max_x: int | None = Query(default=None),
    max_y: int | None = Query(default=None),
) -> AgentsOut:
    engine = _engine(request)
    if None not in (min_x, min_y, max_x, max_y):
        agents = engine.agents_in_bounds(min_x, min_y, max_x, max_y)
    else:
        agents = engine.list_agents()
    return _agents_out(agents)


@app.post("/api/agents/generate", response_model=AgentsOut)
def generate_agents(request: Request, body: GenerateAgentsIn) -> AgentsOut:
    engine = _engine(request)
    try:
        agents = engine.generate_agents(
            body.count,
            body.density,
            origin_x=body.origin_x,
            origin_y=body.origin_y,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _agents_out(agents)


@app.get("/api/agents/{agent_id}/observation", response_model=ObservationOut)
def agent_observation(request: Request, agent_id: int) -> ObservationOut:
    engine = _engine(request)
    try:
        observation = engine.observe(agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    cfg = engine.config
    return ObservationOut(
        observer_id=observation.observer_id,
        vision_radius=cfg.vision_radius,
        interaction_radius=cfg.interaction_radius,
        visible_agents=[
            VisibleAgentOut(
                agent_id=v.agent_id,
                relative_x=v.relative_x,
                relative_y=v.relative_y,
            )
            for v in observation.visible_agents
        ],
    )


_dist = Path(__file__).resolve().parents[3] / "web" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="ui")


def run() -> None:
    import uvicorn

    uvicorn.run("agentiki.server.main:app", host="127.0.0.1", port=8000, reload=False)
