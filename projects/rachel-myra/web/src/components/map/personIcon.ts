// Tiny "restroom sign" person used for patient markers on the maps (instead of round dots).
// One icon per fill/outline pair, built as an SVG data URL for deck.gl's IconLayer.

const W = 48, H = 80; // raster size (2x the 24x40 viewBox, for crisp edges)

const BODY =
  "M7 11h10a2.5 2.5 0 0 1 2.5 2.5V24a1.6 1.6 0 0 1-3.2 0v-8.5h-.8V38a2 2 0 0 1-4 0V27h-1v11a2 2 0 0 1-4 0V15.5h-.8V24a1.6 1.6 0 0 1-3.2 0V13.5A2.5 2.5 0 0 1 7 11z";

const cache = new Map<string, { url: string; width: number; height: number; anchorY: number; id: string }>();

const hex = (c: readonly number[]) => "#" + c.slice(0, 3).map((v) => v.toString(16).padStart(2, "0")).join("");

/** Icon descriptor for IconLayer.getIcon. `fill`/`stroke` are [r,g,b]. Anchored at the feet. */
export function personIcon(fill: readonly number[], stroke: readonly number[] = [255, 255, 255], strokeW = 1.6) {
  const id = `${hex(fill)}-${hex(stroke)}-${strokeW}`;
  let icon = cache.get(id);
  if (!icon) {
    const svg =
      `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="-1.5 -1.5 27 43">` +
      `<g fill="${hex(fill)}" stroke="${hex(stroke)}" stroke-width="${strokeW}" stroke-linejoin="round" paint-order="stroke">` +
      `<circle cx="12" cy="5" r="4.2"/><path d="${BODY}"/></g></svg>`;
    icon = { url: `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`, width: W, height: H, anchorY: H, id };
    cache.set(id, icon);
  }
  return icon;
}
