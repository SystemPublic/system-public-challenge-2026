// Help-place types from community_resources_nyc.geojson, grouped into three families.
// One plain marker shape (a small dot), one muted color per family, no letters.

export type HelpFamily = "cool" | "community" | "services";

export const HELP_FAMILIES: Record<HelpFamily, { label: string; hex: string; rgb: [number, number, number] }> = {
  // Blue: places to cool off. Not green: green read as the teal "Low risk" people. Blue is in
  // neither the risk colors nor the heat ramp (validated: ΔE 18 vs Low teal, normal vision).
  cool: { label: "Places to cool off", hex: "#2563eb", rgb: [37, 99, 235] },
  // Okabe–Ito sky blue: community places (kept small and light so patient dots stay dominant).
  community: { label: "Community places", hex: "#56b4e9", rgb: [86, 180, 233] },
  // Neutral gray: other services.
  services: { label: "Other services", hex: "#8a8a84", rgb: [138, 138, 132] },
};

export const HELP_TYPES: { type: string; label: string; family: HelpFamily; main: boolean }[] = [
  { type: "Cooling center", label: "Cooling centers", family: "cool", main: true },
  { type: "Cool indoor public place", label: "Cool indoor places", family: "cool", main: true },
  { type: "Library", label: "Libraries", family: "cool", main: true },
  { type: "Senior center", label: "Senior centers", family: "community", main: true },
  { type: "Community center", label: "Community centers", family: "community", main: false },
  { type: "Recreation center", label: "Recreation centers", family: "community", main: false },
  { type: "Food pantry / soup kitchen", label: "Food pantries", family: "services", main: false },
  { type: "Community organization", label: "Community groups", family: "services", main: false },
  { type: "Homeless services", label: "Homeless services", family: "services", main: false },
  { type: "Outdoor spray shower / pool", label: "Outdoor showers and pools", family: "cool", main: false },
];

/** Default: only the most relevant places. Everything else sits under "More places". */
export const DEFAULT_HELP_TYPES = HELP_TYPES.filter((t) => t.main).map((t) => t.type);

export function helpFamily(type: string): HelpFamily {
  return HELP_TYPES.find((t) => t.type === type)?.family ?? "services";
}

const cache = new Map<string, string>();
/** A plain dot in the family color (kept for legends and cards). */
export function helpIconUrl(type: string): string {
  const hit = cache.get(type);
  if (hit) return hit;
  const { hex } = HELP_FAMILIES[helpFamily(type)];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><circle cx="16" cy="16" r="11" fill="${hex}" stroke="#ffffff" stroke-width="4"/></svg>`;
  const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  cache.set(type, url);
  return url;
}
