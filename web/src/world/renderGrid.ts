import {
  AXIS_LINE_RGB,
  GRID_LINE_RGB,
  cellColor,
  rgbCss,
} from "./hash";
import { screenCellSize, type Camera } from "./camera";

const CELL_FILL = rgbCss(cellColor());
const GRID_LINE = rgbCss(GRID_LINE_RGB);
const AXIS_LINE = rgbCss(AXIS_LINE_RGB);
/** Outside the fixed map — darker than cells. */
const OUTSIDE_RGB: readonly [number, number, number] = [210, 214, 220];

export type GridRenderOptions = {
  width: number;
  height: number;
  camera: Camera;
  cellPx: number;
  mapWidth: number;
  mapHeight: number;
};

export function renderGrid(
  ctx: CanvasRenderingContext2D,
  opts: GridRenderOptions,
): void {
  const { width, height, camera, cellPx, mapWidth, mapHeight } = opts;
  const size = screenCellSize(cellPx, camera.zoom);
  if (size <= 0) {
    return;
  }

  ctx.save();
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = rgbCss(OUTSIDE_RGB);
  ctx.fillRect(0, 0, width, height);

  const step = size >= 2 ? 1 : Math.max(1, Math.ceil(2 / size));
  const drawSize = size * step;
  const halfW = width / 2;
  const halfH = height / 2;

  const viewMinX = Math.floor(camera.x - halfW / size) - step;
  const viewMaxX = Math.ceil(camera.x + halfW / size) + step;
  const viewMinY = Math.floor(camera.y - halfH / size) - step;
  const viewMaxY = Math.ceil(camera.y + halfH / size) + step;

  const minX = Math.max(viewMinX, 0);
  const maxX = Math.min(viewMaxX, mapWidth - 1);
  const minY = Math.max(viewMinY, 0);
  const maxY = Math.min(viewMaxY, mapHeight - 1);

  if (minX <= maxX && minY <= maxY) {
    for (let y = minY; y <= maxY; y += step) {
      const sy = (y - camera.y) * size + halfH;
      for (let x = minX; x <= maxX; x += step) {
        const sx = (x - camera.x) * size + halfW;
        ctx.fillStyle = CELL_FILL;
        ctx.fillRect(sx, sy, drawSize + 0.5, drawSize + 0.5);
      }
    }

    if (size >= 8) {
      ctx.beginPath();
      ctx.strokeStyle = GRID_LINE;
      ctx.lineWidth = 1;
      const lineMinX = minX;
      const lineMaxX = Math.min(maxX + 1, mapWidth);
      const lineMinY = minY;
      const lineMaxY = Math.min(maxY + 1, mapHeight);
      for (let x = lineMinX; x <= lineMaxX; x += step) {
        const sx = Math.round((x - camera.x) * size + halfW) + 0.5;
        const y0 = (lineMinY - camera.y) * size + halfH;
        const y1 = (lineMaxY - camera.y) * size + halfH;
        ctx.moveTo(sx, y0);
        ctx.lineTo(sx, y1);
      }
      for (let y = lineMinY; y <= lineMaxY; y += step) {
        const sy = Math.round((y - camera.y) * size + halfH) + 0.5;
        const x0 = (lineMinX - camera.x) * size + halfW;
        const x1 = (lineMaxX - camera.x) * size + halfW;
        ctx.moveTo(x0, sy);
        ctx.lineTo(x1, sy);
      }
      ctx.stroke();
    }

    if (size >= 56 && step === 1) {
      ctx.fillStyle = AXIS_LINE;
      ctx.font = "11px ui-sans-serif, system-ui, sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      for (let y = minY; y <= maxY; y += 1) {
        const sy = (y - camera.y) * size + halfH;
        for (let x = minX; x <= maxX; x += 1) {
          const sx = (x - camera.x) * size + halfW;
          ctx.fillText(`${x},${y}`, sx + 6, sy + 6);
        }
      }
    }
  }

  // Map outline
  const left = Math.round((0 - camera.x) * size + halfW) + 0.5;
  const top = Math.round((0 - camera.y) * size + halfH) + 0.5;
  const right = Math.round((mapWidth - camera.x) * size + halfW) + 0.5;
  const bottom = Math.round((mapHeight - camera.y) * size + halfH) + 0.5;
  ctx.beginPath();
  ctx.strokeStyle = AXIS_LINE;
  ctx.lineWidth = 1.5;
  ctx.strokeRect(left, top, right - left, bottom - top);

  ctx.restore();
}
