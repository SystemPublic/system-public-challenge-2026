"use client";

import { useEffect, useState } from "react";

/** One live question to /api/alert/system. Results are shared per query. */
const inflight = new Map<string, Promise<unknown>>();

export type Live<T> = { state: "loading" } | { state: "live"; data: T } | { state: "snapshot"; reason: string };

export function useSystem<T>(query: string | null): Live<T> | null {
  const [res, setRes] = useState<Live<T> | null>(query ? { state: "loading" } : null);
  useEffect(() => {
    if (!query) {
      setRes(null);
      return;
    }
    let alive = true;
    setRes({ state: "loading" });
    let p = inflight.get(query);
    if (!p) {
      p = fetch(`/api/alert/system?${query}`).then((r) => r.json());
      inflight.set(query, p);
    }
    p.then((json) => {
      if (!alive) return;
      const j = json as { live?: boolean; reason?: string };
      if (!j.live) inflight.delete(query); // a failed call is retried next time, not remembered
      setRes(j.live ? { state: "live", data: json as T } : { state: "snapshot", reason: j.reason ?? "unavailable" });
    }).catch(() => {
      inflight.delete(query);
      if (alive) setRes({ state: "snapshot", reason: "call_failed" });
    });
    return () => {
      alive = false;
    };
  }, [query]);
  return res;
}

type LiveAssoc = Record<string, unknown> & { system_id: string; vetted: boolean | null };
export type LiveFinding = { found: boolean; vetted: boolean | null; finding: LiveAssoc | null };
export type LivePaper = {
  pmid: string;
  inGraph: boolean;
  study: { study_id?: string } | null;
  total: number;
  quarantined: number;
  /** Vetted associations only. */
  findings: LiveAssoc[];
};
export type LiveCoverage = {
  papers: { pmid: string; inGraph: boolean; studyId: string | null; total: number; shown: number; quarantined: number }[];
  confirmed: number;
  total: number;
  shown: number;
  quarantined: number;
};
export type LiveStudies = { asked: number; held: { pmid: string; studyId: string | null }[] };
export type LiveProbe = { q: string; count: number; capped: boolean; variables: { system_id: string; name: string }[] };
export type LiveConcept = {
  id: string;
  label: string | null;
  totalRelationships: number;
  shown: number;
  lastPublishedAmongShown: string | null;
  neighbours: { id: string | null; label: string | null; numFindings: number; numStudies: number; lastPublished: string | null }[];
};
