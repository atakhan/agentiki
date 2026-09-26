import type { AgentVisual } from "./agentAnimation";
import { screenCellSize, type Camera } from "./camera";

const AGENT_FILL = "#4a7fd4";
const AGENT_RADIUS_RATIO = 0.35;

export type AgentRenderOptions = {
  width: number;
  height: number;
  camera: Camera;
  cellPx: number;
  agents: readonly AgentVisual[];
};

export function renderAgents(
  ctx: CanvasRenderingContext2D,
  opts: AgentRenderOptions,
): void {
  const { width, height, camera, cellPx, agents } = opts;
  const size = screenCellSize(cellPx, camera.zoom);
  if (size <= 0 || agents.length === 0) {
    return;
  }

  const halfW = width / 2;
  const halfH = height / 2;
  const radius = Math.max(1.5, size * AGENT_RADIUS_RATIO);

  const minX = camera.x - halfW / size - 1;
  const maxX = camera.x + halfW / size + 2;
  const minY = camera.y - halfH / size - 1;
  const maxY = camera.y + halfH / size + 2;

  ctx.save();
  ctx.fillStyle = AGENT_FILL;

  for (const agent of agents) {
    if (
      agent.worldX < minX ||
      agent.worldX > maxX ||
      agent.worldY < minY ||
      agent.worldY > maxY
    ) {
      continue;
    }
    const sx = (agent.worldX - camera.x) * size + halfW;
    const sy = (agent.worldY - camera.y) * size + halfH;
    ctx.beginPath();
    ctx.arc(sx, sy, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.restore();
}
