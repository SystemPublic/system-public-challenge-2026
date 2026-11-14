"use client";

/**
 * Forecast URL state.
 *   area=<ISO3>           selected country (the shell's shared param). A legacy
 *                         `country=<ISO3>` (the Alert tab's back-link) is read
 *                         when present and replaced by `area` on first write.
 *   range=<from>-<to>     the app's shared time range; the as-of year is the
 *                         UPPER bound, clamped. Absent -> MAX_YEAR.
 * Writes start from the live params so unknown params (marker, ...) survive.
 * The as-of year lives in local state so the map responds instantly; it is
 * synced to the URL with a 250 ms debounce (one replace after the user stops).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AREA_PARAM, PARAM, parseTimeRange } from "@/lib/selection";
import { MARKER_ID, MAX_YEAR, MIN_YEAR, clampYear } from "./data";
import { COUNTRY_BY_ISO3 } from "./geo";

export const LEGACY_COUNTRY_PARAM = "country";
/** `layer=papers` shows the "Papers and the Graph" layer; absent = genome. */
export const LAYER_PARAM = "layer";
export type ForecastLayer = "genome" | "papers";
const YEAR_DEBOUNCE_MS = 250;
/** A change within this window of the previous one is part of a run (Play, held key). */
const YEAR_RUN_WINDOW_MS = 1500;
/** During a run, wait past the slowest Play step (1.2 s under reduced motion). */
const YEAR_RUN_DEBOUNCE_MS = 1300;

export function parseCountry(raw: string | null): string | null {
  if (!raw) return null;
  const code = raw.trim().toUpperCase();
  return COUNTRY_BY_ISO3[code] ? code : null;
}

export function parseAsOfYear(raw: string | null): number {
  const r = parseTimeRange(raw);
  return clampYear(r ? r[1] : MAX_YEAR);
}

/**
 * A year and country hinted by the Alert tab's params when `range` is absent:
 *   finding=g:<ISO3>:<year>:...   or   alert=k540e-<ISO3>-<year>-...
 */
export function hintFrom(params: URLSearchParams): { iso3: string | null; year: number } | null {
  const f = /^g:([A-Za-z]{3}):(\d{4})(?::|$)/.exec(params.get("finding") ?? "");
  const a = /^k540e-([A-Za-z]{3})-(\d{4})(?:-|$)/i.exec(params.get("alert") ?? "");
  const m = f ?? a;
  if (!m) return null;
  return { iso3: parseCountry(m[1]), year: clampYear(Number(m[2])) };
}

export function rangeFor(year: number): string {
  return `${MIN_YEAR}-${clampYear(year)}`;
}

export function useForecastUrl() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const rawRange = searchParams.get(PARAM.timeRange);
  // Only used when `range` is absent: an explicit range always wins.
  const hint = useMemo(
    () => (rawRange ? null : hintFrom(new URLSearchParams(searchParams.toString()))),
    [rawRange, searchParams],
  );
  const explicitCountry =
    parseCountry(searchParams.get(LEGACY_COUNTRY_PARAM)) ?? parseCountry(searchParams.get(AREA_PARAM));
  const country = explicitCountry ?? hint?.iso3 ?? null;
  const layer: ForecastLayer = searchParams.get(LAYER_PARAM) === "papers" ? "papers" : "genome";
  const urlYear = useMemo(
    () => (hint ? hint.year : parseAsOfYear(rawRange)),
    [hint, rawRange],
  );

  const [asOfYear, setLocalYear] = useState(urlYear);
  const pendingYearRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastYearCallRef = useRef(0);

  // Follow the URL when it changes from outside (back button, a pasted link).
  useEffect(() => {
    if (pendingYearRef.current === null) setLocalYear(urlYear);
  }, [urlYear]);

  const write = useCallback(
    (patch: Record<string, string | null>) => {
      const p = new URLSearchParams(window.location.search);
      // Fold in a pending year so one action issues exactly one replace.
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = null;
      if (pendingYearRef.current !== null && !(PARAM.timeRange in patch)) {
        p.set(PARAM.timeRange, rangeFor(pendingYearRef.current));
      }
      pendingYearRef.current = null;
      for (const [k, v] of Object.entries(patch)) {
        if (v === null) p.delete(k);
        else p.set(k, v);
      }
      const next = p.toString();
      router.replace(next ? `${pathname}?${next}` : pathname, { scroll: false });
    },
    [pathname, router],
  );

  // A legacy ?country= link, or an Alert-tab link carrying the year in
  // finding/alert: normalise once to ?area= and ?range= so the shell carries them.
  const legacy = searchParams.get(LEGACY_COUNTRY_PARAM);
  const hintKey = hint ? `${hint.iso3}|${hint.year}` : "";
  useEffect(() => {
    if (legacy === null && !hint) return;
    const patch: Record<string, string | null> = {
      [AREA_PARAM]: country ?? searchParams.get(AREA_PARAM),
      [LEGACY_COUNTRY_PARAM]: null,
    };
    if (hint) patch[PARAM.timeRange] = rangeFor(hint.year);
    write(patch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [legacy, hintKey]);

  useEffect(
    () => () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    },
    [],
  );

  const setCountry = useCallback(
    (iso3: string | null) =>
      write({ [AREA_PARAM]: iso3 ? iso3.toUpperCase() : null, [LEGACY_COUNTRY_PARAM]: null }),
    [write],
  );

  const setLayer = useCallback(
    (next: ForecastLayer) => write({ [LAYER_PARAM]: next === "papers" ? "papers" : null }),
    [write],
  );

  const setAsOfYear = useCallback(
    (year: number) => {
      const y = clampYear(year);
      setLocalYear(y);
      pendingYearRef.current = y;
      const now = Date.now();
      const inRun = now - lastYearCallRef.current < YEAR_RUN_WINDOW_MS;
      lastYearCallRef.current = now;
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        const pending = pendingYearRef.current;
        pendingYearRef.current = null;
        if (pending === null) return;
        const p = new URLSearchParams(window.location.search);
        p.set(PARAM.timeRange, rangeFor(pending));
        router.replace(`${pathname}?${p.toString()}`, { scroll: false });
      }, y >= MAX_YEAR ? 0 : inRun ? YEAR_RUN_DEBOUNCE_MS : YEAR_DEBOUNCE_MS);
    },
    [pathname, router],
  );

  /** Write a pending as-of year now (playback paused or ended). */
  const flushYear = useCallback(() => {
    const pending = pendingYearRef.current;
    if (pending === null) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = null;
    pendingYearRef.current = null;
    const p = new URLSearchParams(window.location.search);
    p.set(PARAM.timeRange, rangeFor(pending));
    router.replace(`${pathname}?${p.toString()}`, { scroll: false });
  }, [pathname, router]);

  const hrefForAlert = useCallback(
    (alertId: string) =>
      `/alert?${new URLSearchParams({ alert: alertId, [PARAM.markerId]: MARKER_ID }).toString()}`,
    [],
  );
  const hrefForAlertTab = useMemo(() => {
    const p = new URLSearchParams();
    if (country) p.set(AREA_PARAM, country);
    p.set(PARAM.markerId, MARKER_ID);
    return `/alert?${p.toString()}`;
  }, [country]);

  return {
    country,
    asOfYear,
    layer,
    setLayer,
    setCountry,
    setAsOfYear,
    flushYear,
    hrefForAlert,
    hrefForAlertTab,
  };
}
