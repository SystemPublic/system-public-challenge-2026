// Area selection on the maps (shared by the heat-day time-lapse and the static clinician map;
// no map-library imports, so it is safe to use in server-rendered components).

/** A box on the map in lon/lat (west, south, east, north). Used by the flat time-lapse map. */
export type Area = { w: number; s: number; e: number; n: number };

export const inArea = (a: Area, p: { lon: number; lat: number }) =>
  p.lon >= a.w && p.lon <= a.e && p.lat >= a.s && p.lat <= a.n;

/** The four corners of a dragged screen box, unprojected to [lon, lat]. On a tilted (3D) map the
 *  box covers a trapezoid on the ground, so we test against the corners, not a lon/lat rectangle. */
export type Ring = [number, number][];

export function inRing(ring: Ring, p: { lon: number; lat: number }): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if (yi > p.lat !== yj > p.lat && p.lon < ((xj - xi) * (p.lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
