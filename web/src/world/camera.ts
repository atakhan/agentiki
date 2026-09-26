export const MIN_ZOOM = 0.1;
export const MAX_ZOOM = 4;
export const DEFAULT_CELL_PX = 50;
export const MIN_CELL_PX = 8;
export const MAX_CELL_PX = 200;

export type Camera = {
  x: number;
  y: number;
  zoom: number;
};

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function clampZoom(zoom: number): number {
  return clamp(zoom, MIN_ZOOM, MAX_ZOOM);
}

export function clampCellPx(px: number): number {
  return clamp(Math.round(px), MIN_CELL_PX, MAX_CELL_PX);
}

export function screenCellSize(cellPx: number, zoom: number): number {
  return cellPx * zoom;
}

/** World point currently under a screen pixel (CSS pixels, y-down). */
export function screenToWorld(
  screenX: number,
  screenY: number,
  width: number,
  height: number,
  camera: Camera,
  cellPx: number,
): { x: number; y: number } {
  const size = screenCellSize(cellPx, camera.zoom);
  return {
    x: camera.x + (screenX - width / 2) / size,
    y: camera.y + (screenY - height / 2) / size,
  };
}
