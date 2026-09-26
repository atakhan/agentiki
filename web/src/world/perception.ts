import type { VisibleAgentObs } from "../types/observation";

export function chebyshevDistance(dx: number, dy: number): number {
  return Math.max(Math.abs(dx), Math.abs(dy));
}

export function isInteractable(
  interactionRadius: number,
  relativeX: number,
  relativeY: number,
): boolean {
  const distance = chebyshevDistance(relativeX, relativeY);
  return distance > 0 && distance <= interactionRadius;
}

export function interactableAgentIds(
  visible: readonly VisibleAgentObs[],
  interactionRadius: number,
): Set<number> {
  const ids = new Set<number>();
  for (const agent of visible) {
    if (isInteractable(interactionRadius, agent.relative_x, agent.relative_y)) {
      ids.add(agent.agent_id);
    }
  }
  return ids;
}
