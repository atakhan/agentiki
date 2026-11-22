import type { AgentsResponse } from "./types/agent";
import type { InteractionEvent } from "./types/interaction";
import type { PDRoundEvent } from "./types/pd";
import type { ObservationResponse } from "./types/observation";

export type LifeRules = {
  startHpMin: number;
  startHpMax: number;
  hpTick: number;
  startEnergy: number;
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
  startHpMin: 40,
  startHpMax: 80,
  hpTick: 1,
  startEnergy: 100,
  moveCost: 2,
  stayCost: 1,
  decisionCost: 1,
  roundCost: 1,
  bothCooperate: 3,
  bothDefect: 1,
  defector: 5,
  cooperator: 0,
};

export const DEFAULT_AGENT_COUNT = 100;
export const DEFAULT_AGENT_DENSITY = 1;
export const DEFAULT_MAP_WIDTH = 64;
export const DEFAULT_MAP_HEIGHT = 64;
export const DEFAULT_FOOD_CAPACITY = 50;
export const DEFAULT_FOOD_DENSITY_RADIUS = 3;
export const DEFAULT_FOOD_ENERGY = 10;

export type WorldConfig = {
  name: string;
  count: number;
  density: number;
  mapWidth: number;
  mapHeight: number;
  foodCapacity: number;
  foodDensityRadius: number;
  foodEnergy: number;
  life: LifeRules;
};

export type FoodItem = {
  id: number;
  x: number;
  y: number;
  energy: number;
};

export type FoodResponse = {
  count: number;
  food: FoodItem[];
};

type LifeBody = {
  start_hp_min: number;
  start_hp_max: number;
  hp_tick: number;
  start_energy: number;
  energy_move: number;
  energy_stay: number;
  energy_play_decision: number;
  energy_game: number;
  reward: number;
  punishment: number;
  temptation: number;
  sucker: number;
};

function lifeBody(life: LifeRules): LifeBody {
  return {
    start_hp_min: life.startHpMin,
    start_hp_max: life.startHpMax,
    hp_tick: life.hpTick,
    start_energy: life.startEnergy,
    energy_move: life.moveCost,
    energy_stay: life.stayCost,
    energy_play_decision: life.decisionCost,
    energy_game: life.roundCost,
    reward: life.bothCooperate,
    punishment: life.bothDefect,
    temptation: life.defector,
    sucker: life.cooperator,
  };
}

function lifeFromBody(raw: LifeBody): LifeRules {
  return {
    startHpMin: raw.start_hp_min,
    startHpMax: raw.start_hp_max,
    hpTick: raw.hp_tick,
    startEnergy: raw.start_energy,
    moveCost: raw.energy_move,
    stayCost: raw.energy_stay,
    decisionCost: raw.energy_play_decision,
    roundCost: raw.energy_game,
    bothCooperate: raw.reward,
    bothDefect: raw.punishment,
    defector: raw.temptation,
    cooperator: raw.sucker,
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
  map_width: number;
  map_height: number;
  food_count: number;
  food_capacity: number;
  food_density_radius: number;
  food_energy: number;
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
  food: FoodResponse;
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
  food_consumed: {
    agent_id: number;
    food_id: number;
    x: number;
    y: number;
    energy: number;
    tick: number;
  }[];
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

export async function resetWorld(): Promise<WorldInfo> {
  const res = await fetch("/api/world/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return (await res.json()) as WorldInfo;
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

export async function fetchFood(): Promise<FoodResponse> {
  const res = await fetch("/api/food");
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return (await res.json()) as FoodResponse;
}

export async function generateAgents(
  config: Pick<
    WorldConfig,
    | "count"
    | "density"
    | "life"
    | "mapWidth"
    | "mapHeight"
    | "foodCapacity"
    | "foodDensityRadius"
    | "foodEnergy"
  >,
): Promise<AgentsResponse> {
  const res = await fetch("/api/agents/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      count: config.count,
      density: config.density,
      map_width: config.mapWidth,
      map_height: config.mapHeight,
      food_capacity: config.foodCapacity,
      food_density_radius: config.foodDensityRadius,
      food_energy: config.foodEnergy,
      life: lifeBody(config.life),
    }),
  });
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return (await res.json()) as AgentsResponse;
}

export async function listWorldConfigs(): Promise<string[]> {
  const res = await fetch("/api/world-configs");
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  const body = (await res.json()) as { names: string[] };
  return body.names;
}

export async function loadWorldConfig(name: string): Promise<WorldConfig> {
  const res = await fetch(`/api/world-configs/${encodeURIComponent(name)}`);
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  const body = (await res.json()) as {
    name: string;
    count: number;
    density: number;
    map_width?: number;
    map_height?: number;
    food_capacity?: number;
    food_density_radius?: number;
    food_energy?: number;
    life: LifeBody;
  };
  return {
    name: body.name,
    count: body.count,
    density: body.density,
    mapWidth: body.map_width ?? DEFAULT_MAP_WIDTH,
    mapHeight: body.map_height ?? DEFAULT_MAP_HEIGHT,
    foodCapacity: body.food_capacity ?? DEFAULT_FOOD_CAPACITY,
    foodDensityRadius: body.food_density_radius ?? DEFAULT_FOOD_DENSITY_RADIUS,
    foodEnergy: body.food_energy ?? DEFAULT_FOOD_ENERGY,
    life: lifeFromBody(body.life),
  };
}

export async function saveWorldConfig(config: WorldConfig): Promise<WorldConfig> {
  const res = await fetch(
    `/api/world-configs/${encodeURIComponent(config.name)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: config.name,
        count: config.count,
        density: config.density,
        map_width: config.mapWidth,
        map_height: config.mapHeight,
        food_capacity: config.foodCapacity,
        food_density_radius: config.foodDensityRadius,
        food_energy: config.foodEnergy,
        life: lifeBody(config.life),
      }),
    },
  );
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  const body = (await res.json()) as {
    name: string;
    count: number;
    density: number;
    map_width: number;
    map_height: number;
    food_capacity: number;
    food_density_radius: number;
    food_energy: number;
    life: LifeBody;
  };
  return {
    name: body.name,
    count: body.count,
    density: body.density,
    mapWidth: body.map_width,
    mapHeight: body.map_height,
    foodCapacity: body.food_capacity,
    foodDensityRadius: body.food_density_radius,
    foodEnergy: body.food_energy,
    life: lifeFromBody(body.life),
  };
}
