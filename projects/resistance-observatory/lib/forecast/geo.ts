import world from "@/data/forecast/geo/world.json";

export interface GeoCountry {
  iso3: string;
  name: string;
  aliases: string[];
  continent: string;
  d: string;
  bbox: [number, number, number, number];
  center: [number, number];
  tiny: boolean;
}
export interface GeoPlace { name: string; ascii: string; iso3: string; pop: number; capital: boolean }

const raw = world as unknown as {
  source: { id: string; label: string; licence: string; url: string };
  projection: string;
  width: number;
  height: number;
  countries: GeoCountry[];
};

export const WORLD: { width: number; height: number; projection: string; countries: GeoCountry[] } = {
  width: raw.width,
  height: raw.height,
  projection: raw.projection,
  countries: raw.countries,
};

export const GEO_SOURCE: { id: string; label: string; licence: string; url: string } = {
  id: raw.source.id,
  label: raw.source.label,
  licence: raw.source.licence,
  url: raw.source.url,
};

export const COUNTRY_BY_ISO3: Record<string, GeoCountry> = Object.fromEntries(
  raw.countries.map((c) => [c.iso3, c]),
);

export function countryName(iso3: string): string {
  return COUNTRY_BY_ISO3[iso3]?.name ?? iso3;
}

let placesCache: Promise<GeoPlace[]> | null = null;

/** Lazy: dynamic import of places.json, mapped to objects, cached after the first call. */
export function loadPlaces(): Promise<GeoPlace[]> {
  if (!placesCache) {
    placesCache = import("@/data/forecast/geo/places.json").then((m) => {
      const rows = (m as unknown as { default: { places: [string, string, string, number, number][] } }).default.places;
      return rows.map(([name, ascii, iso3, pop, capital]) => ({ name, ascii, iso3, pop, capital: capital === 1 }));
    });
  }
  return placesCache;
}
