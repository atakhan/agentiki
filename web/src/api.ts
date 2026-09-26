import type { AgentsResponse } from "./types/agent";
import type { InteractionEvent } from "./types/interaction";
import type { PDRoundEvent } from "./types/pd";
import type { ObservationResponse } from "./types/observation";

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

export async function stepWorld(n: number = 1): Promise<StepResponse> {
  const res = await fetch("/api/world/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ n }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`world step failed: ${res.status} ${detail}`);
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
): Promise<AgentsResponse> {
  const res = await fetch("/api/agents/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count, density }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`agents generate failed: ${res.status} ${detail}`);
  }
  return (await res.json()) as AgentsResponse;
}
