"use client";

// Confirmations: all cross-concept pairs with published associations whose
// endpoints map to NYC measures and whose city correlation agrees with (or
// doesn't contradict) the published effects — the opposite-direction pairs
// live on the Contested tab. Searchable/sortable table; click a row to expand
// the pair's correlation maps + ego graph + evidence just below the row.

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type {
  ConceptDict,
  ConfirmationRow,
  District,
  DistrictValue,
  Ego,
  MeasureDict,
} from "@/lib/bundle";
import { fmtInt } from "@/lib/format";
import { PairTable, type SortKey } from "@/components/pair-table";

export default function ConfirmationsApp({
  confirmations,
  concepts,
  measures,
  egos,
  districts,
  values,
}: {
  confirmations: ConfirmationRow[];
  concepts: ConceptDict;
  measures: MeasureDict;
  egos: Record<string, Ego>;
  districts: District[];
  values: Record<string, Record<string, DistrictValue>>;
}) {
  const search = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [sort, setSort] = useState<{ k: SortKey; dir: number }>({ k: "na", dir: -1 });
  const [fRho, setFRho] = useState(true);
  const [fMod, setFMod] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 120);
    return () => clearTimeout(t);
  }, [q]);

  const mlabel = (mid: string) => measures[mid]?.l ?? mid;
  const label = (cid: string) => concepts[cid]?.l || cid;

  // the base set: everything except the direction-contested pairs
  const base = useMemo(
    () => confirmations.filter((r) => r.agree !== "opposite"),
    [confirmations],
  );

  const rows = useMemo(() => {
    const hay = (r: ConfirmationRow) =>
      [
        label(r.c1),
        concepts[r.c1]?.dm,
        label(r.c2),
        concepts[r.c2]?.dm,
        r.m1.map(mlabel).join(" "),
        r.m2.map(mlabel).join(" "),
        r.note,
        r.et.join(" "),
      ]
        .join(" ")
        .toLowerCase();
    const q0 = debouncedQ.trim().toLowerCase();
    let out = base;
    if (q0) out = out.filter((r) => hay(r).includes(q0));
    if (fRho) out = out.filter((r) => r.rho !== null);
    if (fMod) out = out.filter((r) => r.rho !== null && r.mod);
    const val = (r: ConfirmationRow) => {
      if (sort.k === "l1") return label(r.c1);
      if (sort.k === "l2") return label(r.c2);
      if (sort.k === "check") return r.chk ? r.chk.map(mlabel).join("+") : "";
      if (sort.k === "dir") return r.dir === null ? 0 : r.dir;
      return r[sort.k] === null ? -Infinity : (r[sort.k] as number);
    };
    return [...out].sort((a, b) => {
      const va = val(a);
      const vb = val(b);
      const c = typeof va === "string" ? va.localeCompare(vb as string) : (va as number) - (vb as number);
      return c * sort.dir;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base, concepts, measures, debouncedQ, fRho, fMod, sort]);

  const selPair = search.get("pair");
  const pair =
    selPair !== null
      ? confirmations.find(
          (r) => selPair === `${r.c1}|${r.c2}` || selPair === `${r.c2}|${r.c1}`,
        )
      : null;

  const setPair = (c1: string, c2: string) => {
    router.replace(`${pathname}?pair=${encodeURIComponent(`${c1}|${c2}`)}`, {
      scroll: false,
    });
  };
  const closePair = () => router.replace(pathname, { scroll: false });

  const toggleSort = (k: SortKey) => {
    setSort((s) =>
      s.k === k
        ? { k, dir: -s.dir }
        : { k, dir: k === "l1" || k === "l2" || k === "check" ? 1 : -1 },
    );
  };

  return (
    <div className="mt-8">
      <div className="flex flex-wrap items-center gap-4">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search concepts, domains, measures…"
          className="dash-select flex-[1_1_260px] max-w-[420px] py-1.5"
          aria-label="Search confirmations"
        />
        <label className="flex items-center gap-1.5 font-sans text-[0.78rem] text-[color:var(--chart-ink-2)]">
          <input type="checkbox" checked={fRho} onChange={(e) => setFRho(e.target.checked)} />
          has city ρ
        </label>
        <label className="flex items-center gap-1.5 font-sans text-[0.78rem] text-[color:var(--chart-ink-2)]">
          <input type="checkbox" checked={fMod} onChange={(e) => setFMod(e.target.checked)} />
          modeled ρ only
        </label>
        <span className="ml-auto font-sans text-[0.72rem] text-muted">
          {fmtInt(rows.length)} of {fmtInt(confirmations.length)} pairs
        </span>
      </div>

      <PairTable
        rows={rows}
        sort={sort}
        onSort={toggleSort}
        selKey={pair ? `${pair.c1}|${pair.c2}` : null}
        onOpen={(r) => {
          const isOpen =
            pair != null &&
            ((pair.c1 === r.c1 && pair.c2 === r.c2) ||
              (pair.c1 === r.c2 && pair.c2 === r.c1));
          if (isOpen) closePair();
          else setPair(r.c1, r.c2);
        }}
        onClose={closePair}
        concepts={concepts}
        measures={measures}
        egos={egos}
        districts={districts}
        values={values}
      />
    </div>
  );
}
