"use client";

// Contested: the pairs whose district-level city correlation points OPPOSITE
// to the direction the SPG effects imply — same table as confirmations, one
// filter apart. Clicking a row expands the same correlation-maps + ego-graph
// popup below it.

import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type {
  ConceptDict,
  ConfirmationRow,
  District,
  DistrictValue,
  Ego,
  MeasureDict,
} from "@/lib/bundle";
import { PairTable, type SortKey } from "@/components/pair-table";

export default function ContestedApp({
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

  const [sort, setSort] = useState<{ k: SortKey; dir: number }>({ k: "rho", dir: -1 });

  const rows = useMemo(
    () => confirmations.filter((r) => r.agree === "opposite"),
    [confirmations],
  );

  const mlabel = (mid: string) => measures[mid]?.l ?? mid;
  const label = (cid: string) => concepts[cid]?.l || cid;

  const sorted = useMemo(() => {
    const val = (r: ConfirmationRow) => {
      if (sort.k === "l1") return label(r.c1);
      if (sort.k === "l2") return label(r.c2);
      if (sort.k === "check") return r.chk ? r.chk.map(mlabel).join("+") : "";
      if (sort.k === "dir") return r.dir === null ? 0 : r.dir;
      return r[sort.k] === null ? -Infinity : (r[sort.k] as number);
    };
    return [...rows].sort((a, b) => {
      const va = val(a);
      const vb = val(b);
      const c = typeof va === "string" ? va.localeCompare(vb as string) : (va as number) - (vb as number);
      return c * sort.dir;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, concepts, measures, sort]);

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
      <PairTable
        rows={sorted}
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
