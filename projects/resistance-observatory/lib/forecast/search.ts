import type { GeoCountry, GeoPlace } from "./geo";
import { countryName } from "./geo";

export type SearchResult = {
  kind: "country" | "city";
  iso3: string;
  label: string;
  sublabel: string;
  cityName: string | null;
};

export function norm(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[’`]/g, "'")
    .trim();
}

export function searchAll(
  query: string,
  countries: GeoCountry[],
  places: GeoPlace[],
  limit = 8,
): SearchResult[] {
  const q = norm(query);
  if (!q) return [];
  const scored: { rank: number; r: SearchResult }[] = [];
  for (const c of countries) {
    const names = [c.name, ...c.aliases].map(norm);
    let rank = -1;
    if (names.some((n) => n === q)) rank = 0;
    else if (names.some((n) => n.startsWith(q))) rank = 1;
    else if (names.some((n) => n.includes(q))) rank = 2;
    if (rank >= 0) {
      scored.push({
        rank,
        r: { kind: "country", iso3: c.iso3, label: c.name, sublabel: "Country", cityName: null },
      });
    }
  }
  scored.sort((a, b) => a.rank - b.rank || a.r.label.localeCompare(b.r.label));
  const out = scored.map((s) => s.r);
  if (out.length < limit) {
    const pre: { pop: number; p: GeoPlace }[] = [];
    const sub: { pop: number; p: GeoPlace }[] = [];
    for (const p of places) {
      const n = norm(p.name);
      const a = norm(p.ascii);
      if (n.startsWith(q) || a.startsWith(q)) pre.push({ pop: p.pop, p });
      else if (n.includes(q) || a.includes(q)) sub.push({ pop: p.pop, p });
    }
    pre.sort((a, b) => b.pop - a.pop);
    sub.sort((a, b) => b.pop - a.pop);
    for (const { p } of [...pre, ...sub]) {
      if (out.length >= limit) break;
      out.push({
        kind: "city",
        iso3: p.iso3,
        label: p.name,
        sublabel: `City in ${countryName(p.iso3)} · opens the country view`,
        cityName: p.name,
      });
    }
  }
  return out.slice(0, limit);
}
