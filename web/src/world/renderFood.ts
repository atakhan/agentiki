import { screenCellSize, type Camera } from "./camera";

const FOOD_FILL = "#3d9e5f";

export type FoodItem = {
  id: number;
  x: number;
  y: number;
  energy: number;
};

export type FoodRenderOptions = {
  width: number;
  height: number;
  camera: Camera;
  cellPx: number;
  food: readonly FoodItem[];
};

export function renderFood(
  ctx: CanvasRenderingContext2D,
  opts: FoodRenderOptions,
): void {
  const { width, height, camera, cellPx, food } = opts;
  const size = screenCellSize(cellPx, camera.zoom);
  if (size <= 0 || food.length === 0) {
    return;
  }

  const halfW = width / 2;
  const halfH = height / 2;
  const radius = Math.max(1.2, size * 0.18);

  const minX = camera.x - halfW / size - 1;
  const maxX = camera.x + halfW / size + 2;
  const minY = camera.y - halfH / size - 1;
  const maxY = camera.y + halfH / size + 2;

  ctx.save();
  ctx.fillStyle = FOOD_FILL;

  for (const item of food) {
    const worldX = item.x + 0.5;
    const worldY = item.y + 0.5;
    if (worldX < minX || worldX > maxX || worldY < minY || worldY > maxY) {
      continue;
    }
    const sx = (worldX - camera.x) * size + halfW;
    const sy = (worldY - camera.y) * size + halfH;
    ctx.beginPath();
    ctx.arc(sx, sy, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.restore();
}
