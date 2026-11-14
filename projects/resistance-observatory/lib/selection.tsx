"use client";

/**
 * Shared selection state for every tab.
 *
 *   { markerId, timeRange, selectedFindingId }
 *
 * The URL is the single source of truth (CLAUDE.md: "No localStorage for app
 * data. URL params only."). Reading comes from the query string; writing
 * replaces the query string. A copied link therefore restores the selection,
 * and moving between tabs never requires re-selecting anything.
 *
 * Query params:
 *   ?marker=<markerId>
 *   &range=<from>-<to>        (two integers, e.g. a year range)
 *   &finding=<selectedFindingId>
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

export type TimeRange = [number, number];

export type Selection = {
  markerId: string | null;
  timeRange: TimeRange | null;
  selectedFindingId: string | null;
};

export type SelectionContextValue = Selection & {
  /** Merge a partial update into the selection. `null` clears a field. */
  setSelection: (patch: Partial<Selection>) => void;
  setMarkerId: (markerId: string | null) => void;
  setTimeRange: (timeRange: TimeRange | null) => void;
  setSelectedFindingId: (selectedFindingId: string | null) => void;
  /** ISO3 area code from `?area=`, upper-cased; null when absent or malformed.
   *  Not part of the selection: Forecast and Alert own it, the shell only
   *  carries it. */
  area: string | null;
  /** Build an href to another route that carries the current selection, plus
   *  the current `area` (pass `opts.area` to set it, or null to drop it). */
  hrefWithSelection: (
    pathname: string,
    patch?: Partial<Selection>,
    opts?: { area?: string | null },
  ) => string;
};

export const PARAM = {
  markerId: "marker",
  timeRange: "range",
  selectedFindingId: "finding",
} as const;

/** Passthrough param: an ISO 3166-1 alpha-3 code, e.g. `area=MWI`. */
export const AREA_PARAM = "area";

export function parseArea(raw: string | null | undefined): string | null {
  return raw && /^[A-Za-z]{3}$/.test(raw) ? raw.toUpperCase() : null;
}

export function parseTimeRange(raw: string | null): TimeRange | null {
  if (!raw) return null;
  const m = /^(-?\d+)-(-?\d+)$/.exec(raw);
  if (!m) return null;
  const a = Number(m[1]);
  const b = Number(m[2]);
  if (!Number.isFinite(a) || !Number.isFinite(b)) return null;
  return a <= b ? [a, b] : [b, a];
}

export function selectionFromParams(params: URLSearchParams): Selection {
  return {
    markerId: params.get(PARAM.markerId) || null,
    timeRange: parseTimeRange(params.get(PARAM.timeRange)),
    selectedFindingId: params.get(PARAM.selectedFindingId) || null,
  };
}

export function selectionToParams(
  sel: Selection,
  base?: URLSearchParams,
): URLSearchParams {
  const p = new URLSearchParams(base?.toString() ?? "");
  const put = (k: string, v: string | null) => (v ? p.set(k, v) : p.delete(k));
  put(PARAM.markerId, sel.markerId);
  put(PARAM.timeRange, sel.timeRange ? `${sel.timeRange[0]}-${sel.timeRange[1]}` : null);
  put(PARAM.selectedFindingId, sel.selectedFindingId);
  return p;
}

const SelectionContext = createContext<SelectionContextValue | null>(null);

export function SelectionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const current = useMemo(
    () => selectionFromParams(new URLSearchParams(searchParams.toString())),
    [searchParams],
  );

  const area = useMemo(() => parseArea(searchParams.get(AREA_PARAM)), [searchParams]);

  const hrefWithSelection = useCallback(
    (target: string, patch: Partial<Selection> = {}, opts: { area?: string | null } = {}) => {
      const next = { ...current, ...patch };
      const params = selectionToParams(next);
      const nextArea = opts.area === undefined ? area : parseArea(opts.area);
      if (nextArea) params.set(AREA_PARAM, nextArea);
      const qs = params.toString();
      return qs ? `${target}?${qs}` : target;
    },
    [current, area],
  );

  const setSelection = useCallback(
    (patch: Partial<Selection>) => {
      const next = { ...current, ...patch };
      const qs = selectionToParams(
        next,
        new URLSearchParams(searchParams.toString()),
      ).toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [current, pathname, router, searchParams],
  );

  const value = useMemo<SelectionContextValue>(
    () => ({
      ...current,
      area,
      setSelection,
      setMarkerId: (markerId) => setSelection({ markerId }),
      setTimeRange: (timeRange) => setSelection({ timeRange }),
      setSelectedFindingId: (selectedFindingId) =>
        setSelection({ selectedFindingId }),
      hrefWithSelection,
    }),
    [current, area, setSelection, hrefWithSelection],
  );

  return (
    <SelectionContext.Provider value={value}>
      {children}
    </SelectionContext.Provider>
  );
}

/** Read and write the shared selection. Must be used under <SelectionProvider>. */
export function useSelection(): SelectionContextValue {
  const ctx = useContext(SelectionContext);
  if (!ctx) {
    throw new Error("useSelection() must be used inside <SelectionProvider>.");
  }
  return ctx;
}
