import {
  AXIS_LINE_RGB,
  CELL_RGB,
  GRID_LINE_RGB,
  cellColor,
  rgbCss,
} from "./hash";
import { screenCellSize, type Camera } from "./camera";

const CELL_FILL = rgbCss(cellColor());
const GRID_LINE = rgbCss(GRID_LINE_RGB);
const AXIS_LINE = rgbCss(AXIS_LINE_RGB);

export type GridRenderOptions = {
  width: number;
  height: number;
  camera: Camera;
  cellPx: number;
};

export function renderGrid(
  ctx: CanvasRenderingContext2D,
  opts: GridRenderOptions,
): void {
  const { width, height, camera, cellPx } = opts;
  const size = screenCellSize(cellPx, camera.zoom);
  if (size <= 0) {
    return;
  }

  ctx.save();
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = rgbCss(CELL_RGB);
  ctx.fillRect(0, 0, width, height);

  const step = size >= 2 ? 1 : Math.max(1, Math.ceil(2 / size));
  const drawSize = size * step;
  const halfW = width / 2;
  const halfH = height / 2;

  const minX = Math.floor(camera.x - halfW / size) - step;
  const maxX = Math.ceil(camera.x + halfW / size) + step;
  const minY = Math.floor(camera.y - halfH / size) - step;
  const maxY = Math.ceil(camera.y + halfH / size) + step;

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
    for (let x = minX; x <= maxX + 1; x += step) {
      const sx = Math.round((x - camera.x) * size + halfW) + 0.5;
      ctx.moveTo(sx, 0);
      ctx.lineTo(sx, height);
    }
    for (let y = minY; y <= maxY + 1; y += step) {
      const sy = Math.round((y - camera.y) * size + halfH) + 0.5;
      ctx.moveTo(0, sy);
      ctx.lineTo(width, sy);
    }
    ctx.stroke();
  }

  const axisX = Math.round((0 - camera.x) * size + halfW) + 0.5;
  const axisY = Math.round((0 - camera.y) * size + halfH) + 0.5;
  ctx.beginPath();
  ctx.strokeStyle = AXIS_LINE;
  ctx.lineWidth = 1.5;
  ctx.moveTo(axisX, 0);
  ctx.lineTo(axisX, height);
  ctx.moveTo(0, axisY);
  ctx.lineTo(width, axisY);
  ctx.stroke();

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

  ctx.restore();
}
