import type { Agent } from "../types/agent";
import type { VisibleAgentObs } from "../types/observation";
import { interactableAgentIds } from "./perception";
import { screenCellSize, type Camera } from "./camera";

const VISION_FILL = "rgba(74, 127, 212, 0.08)";
const VISION_STROKE = "rgba(74, 127, 212, 0.35)";
const INTERACTION_FILL = "rgba(46, 160, 67, 0.1)";
const INTERACTION_STROKE = "rgba(46, 160, 67, 0.45)";
const VISIBLE_RING = "rgba(74, 127, 212, 0.85)";
const INTERACT_RING = "rgba(46, 160, 67, 0.95)";
const SELECTED_RING = "rgba(220, 80, 60, 0.95)";

export type VisionDebugOptions = {
  width: number;
  height: number;
  camera: Camera;
  cellPx: number;
  selectedAgent: Agent | null;
  visionRadius: number;
  interactionRadius: number;
  visibleAgents: readonly VisibleAgentObs[];
  agentVisuals: ReadonlyMap<number, { worldX: number; worldY: number }>;
};

function worldToScreen(
  wx: number,
  wy: number,
  width: number,
  height: number,
  camera: Camera,
  size: number,
): { x: number; y: number } {
  return {
    x: (wx - camera.x) * size + width / 2,
    y: (wy - camera.y) * size + height / 2,
  };
}

function drawChebyshevSquare(
  ctx: CanvasRenderingContext2D,
  centerCellX: number,
  centerCellY: number,
  radius: number,
  width: number,
  height: number,
  camera: Camera,
  size: number,
  fill: string,
  stroke: string,
) {
  const minX = centerCellX - radius;
  const maxX = centerCellX + radius + 1;
  const minY = centerCellY - radius;
  const maxY = centerCellY + radius + 1;
  const topLeft = worldToScreen(minX, minY, width, height, camera, size);
  const bottomRight = worldToScreen(maxX, maxY, width, height, camera, size);
  const w = bottomRight.x - topLeft.x;
  const h = bottomRight.y - topLeft.y;
  ctx.fillStyle = fill;
  ctx.fillRect(topLeft.x, topLeft.y, w, h);
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 1.5;
  ctx.strokeRect(topLeft.x + 0.5, topLeft.y + 0.5, w - 1, h - 1);
}

export function renderVisionDebug(
  ctx: CanvasRenderingContext2D,
  opts: VisionDebugOptions,
): void {
  const {
    width,
    height,
    camera,
    cellPx,
    selectedAgent,
    visionRadius,
    interactionRadius,
    visibleAgents,
    agentVisuals,
  } = opts;

  if (!selectedAgent) {
    return;
  }

  const size = screenCellSize(cellPx, camera.zoom);
  if (size <= 0) {
    return;
  }

  const interactable = interactableAgentIds(visibleAgents, interactionRadius);

  ctx.save();

  drawChebyshevSquare(
    ctx,
    selectedAgent.x,
    selectedAgent.y,
    visionRadius,
    width,
    height,
    camera,
    size,
    VISION_FILL,
    VISION_STROKE,
  );

  if (interactionRadius > 0) {
    drawChebyshevSquare(
      ctx,
      selectedAgent.x,
      selectedAgent.y,
      interactionRadius,
      width,
      height,
      camera,
      size,
      INTERACTION_FILL,
      INTERACTION_STROKE,
    );
  }

  const radius = Math.max(2, size * 0.38);

  for (const agent of visibleAgents) {
    const visual = agentVisuals.get(agent.agent_id);
    if (!visual) {
      continue;
    }
    const { x: sx, y: sy } = worldToScreen(
      visual.worldX,
      visual.worldY,
      width,
      height,
      camera,
      size,
    );
    ctx.beginPath();
    ctx.strokeStyle = interactable.has(agent.agent_id)
      ? INTERACT_RING
      : VISIBLE_RING;
    ctx.lineWidth = 2;
    ctx.arc(sx, sy, radius + 2, 0, Math.PI * 2);
    ctx.stroke();
  }

  const selectedVisual = agentVisuals.get(selectedAgent.id);
  if (selectedVisual) {
    const { x: sx, y: sy } = worldToScreen(
      selectedVisual.worldX,
      selectedVisual.worldY,
      width,
      height,
      camera,
      size,
    );
    ctx.beginPath();
    ctx.strokeStyle = SELECTED_RING;
    ctx.lineWidth = 2.5;
    ctx.arc(sx, sy, radius + 4, 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.restore();
}
