import type { Agent } from "../types/agent";

export const MOVE_ANIMATION_MS = 500;

export type AgentVisual = {
  id: number;
  worldX: number;
  worldY: number;
};

type AgentAnimation = {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  startTime: number;
};

export function agentWorldPos(agent: Agent): { x: number; y: number } {
  return { x: agent.x + agent.pos_x, y: agent.y + agent.pos_y };
}

export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export class AgentAnimationController {
  private display = new Map<number, { x: number; y: number }>();
  private animations = new Map<number, AgentAnimation>();

  isAnimating(): boolean {
    return this.animations.size > 0;
  }

  reset(): void {
    this.display.clear();
    this.animations.clear();
  }

  syncAgents(agents: readonly Agent[], now = performance.now()): void {
    const seen = new Set<number>();

    for (const agent of agents) {
      seen.add(agent.id);
      const target = agentWorldPos(agent);
      const current = this.display.get(agent.id);

      if (!current) {
        this.display.set(agent.id, target);
        continue;
      }

      const active = this.animations.get(agent.id);
      const from = active ? this.sample(active, now) : current;

      if (
        Math.abs(target.x - from.x) > 1e-6 ||
        Math.abs(target.y - from.y) > 1e-6
      ) {
        this.animations.set(agent.id, {
          fromX: from.x,
          fromY: from.y,
          toX: target.x,
          toY: target.y,
          startTime: now,
        });
      }
    }

    for (const id of this.display.keys()) {
      if (!seen.has(id)) {
        this.display.delete(id);
        this.animations.delete(id);
      }
    }
  }

  getVisuals(agents: readonly Agent[], now = performance.now()): AgentVisual[] {
    const visuals: AgentVisual[] = [];

    for (const agent of agents) {
      const anim = this.animations.get(agent.id);
      if (anim) {
        const pos = this.sample(anim, now);
        this.display.set(agent.id, pos);
        if (this.isComplete(anim, now)) {
          this.animations.delete(agent.id);
        }
        visuals.push({ id: agent.id, worldX: pos.x, worldY: pos.y });
        continue;
      }

      const pos = this.display.get(agent.id) ?? agentWorldPos(agent);
      this.display.set(agent.id, pos);
      visuals.push({ id: agent.id, worldX: pos.x, worldY: pos.y });
    }

    return visuals;
  }

  private sample(anim: AgentAnimation, now: number): { x: number; y: number } {
    const t = Math.min(1, (now - anim.startTime) / MOVE_ANIMATION_MS);
    const eased = easeInOutCubic(t);
    return {
      x: anim.fromX + (anim.toX - anim.fromX) * eased,
      y: anim.fromY + (anim.toY - anim.fromY) * eased,
    };
  }

  private isComplete(anim: AgentAnimation, now: number): boolean {
    return now - anim.startTime >= MOVE_ANIMATION_MS;
  }
}
