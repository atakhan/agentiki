function u32(n: number): number {
  return n >>> 0;
}

function mix32(h: number): number {
  h = u32(h);
  h = u32(h ^ (h >>> 16));
  h = Math.imul(h, 0x7feb352d) >>> 0;
  h = u32(h ^ (h >>> 15));
  h = Math.imul(h, 0x846ca68b) >>> 0;
  h = u32(h ^ (h >>> 16));
  return h;
}

export function cellHash(x: number, y: number, seed: number): number {
  let h = u32(seed);
  h = u32(h + Math.imul(u32(x), 0x9e3779b1));
  h = u32(h ^ u32(y));
  h = u32(h + Math.imul(u32(y), 0x85ebca77));
  return mix32(h);
}

/** Uniform gray for every cell (matches Python sim core). */
export const CELL_RGB: readonly [number, number, number] = [232, 234, 237];

/** Grid lines — slightly darker than cell fill. */
export const GRID_LINE_RGB: readonly [number, number, number] = [210, 213, 218];

/** Axes and labels — a bit more contrast than grid lines. */
export const AXIS_LINE_RGB: readonly [number, number, number] = [185, 189, 196];

export function cellColor(): [number, number, number] {
  return [...CELL_RGB];
}

export function rgbCss(rgb: readonly [number, number, number]): string {
  return `rgb(${rgb[0]} ${rgb[1]} ${rgb[2]})`;
}
