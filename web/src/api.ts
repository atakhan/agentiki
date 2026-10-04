import type { AgentsResponse } from "./types/agent";
import type { InteractionEvent } from "./types/interaction";
import type { PDRoundEvent } from "./types/pd";
import type { ObservationResponse } from "./types/observation";

export type LifeRules = {
  startHp: number;
  moveCost: number;
  stayCost: number;
  decisionCost: number;
  roundCost: number;
  bothCooperate: number;
  bothDefect: number;
  defector: number;
  cooperator: number;
};

export const DEFAULT_LIFE_RULES: LifeRules = {
  startHp: 60,
  moveCost: 2,
  stayCost: 1,
  decisionCost: 1,
  roundCost: 1,
  bothCooperate: 3,
  bothDefect: 1,
  defector: 5,
  cooperator: 0,
};

type LifeBody = {
  start_hp: number;
  hp_move: number;
  hp_stay: number;
  hp_play_decision: number;
  hp_game: number;
  reward: number;
  punishment: number;
  temptation: number;
  sucker: number;
};

function lifeBody(life: LifeRules): LifeBody {
  return {
    start_hp: life.startHp,
    hp_move: life.moveCost,
    hp_stay: life.stayCost,
    hp_play_decision: life.decisionCost,
    hp_game: life.roundCost,
    reward: life.bothCooperate,
    punishment: life.bothDefect,
    temptation: life.defector,
    sucker: life.cooperator,
  };
}

export async function readApiError(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const body = JSON.parse(text) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // not JSON
  }
  return text || `ошибка ${res.status}`;
}

export type WorldInfo = {
  backend: string;
  seed: number;
  tick: number;
  spatial_cell_size: number;
  default_cell_px: number;
  agent_count: number;
  vision_radius: number;
  interaction_radius: number;
};

export async function fetchWorld(): Promise<WorldInfo> {
  const res = await fetch("/api/world");
  if (!res.ok) {
    throw new Error(`world fetch failed: ${res.status}`);
  }
  return (await res.json()) as WorldInfo;
}

export async function fetchAgents(): Promise<AgentsResponse> {
  const res = await fetch("/api/agents");
  if (!res.ok) {
    throw new Error(`agents fetch failed: ${res.status}`);
  }
  return (await res.json()) as AgentsResponse;
}

export type StepResponse = {
  world: WorldInfo;
  agents: AgentsResponse;
  interactions: InteractionEvent[];
  meetings_started: {
    meeting_id: number;
    agent_a_id: number;
    agent_b_id: number;
    round_number: number;
    status: string;
    started_tick: number;
  }[];
  pd_rounds: PDRoundEvent[];
};

export async function stepWorld(
  n: number = 1,
  life: LifeRules = DEFAULT_LIFE_RULES,
): Promise<StepResponse> {
  const res = await fetch("/api/world/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ n, life: lifeBody(life) }),
  });
  if (!res.ok) {
    const detail = await readApiError(res);
    throw new Error(detail);
  }
  return (await res.json()) as StepResponse;
}

export async function fetchObservation(
  agentId: number,
): Promise<ObservationResponse> {
  const res = await fetch(`/api/agents/${agentId}/observation`);
  if (!res.ok) {
    throw new Error(`observation fetch failed: ${res.status}`);
  }
  return (await res.json()) as ObservationResponse;
}

export async function generateAgents(
  count: number,
  density: number,
  life: LifeRules = DEFAULT_LIFE_RULES,
): Promise<AgentsResponse> {
  const res = await fetch("/api/agents/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count, density, life: lifeBody(life) }),
  });
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return (await res.json()) as AgentsResponse;
}
