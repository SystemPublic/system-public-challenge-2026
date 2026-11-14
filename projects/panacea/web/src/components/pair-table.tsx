"use client";

// The sortable table shared by the confirmations and contested tabs. Rows are
// pre-filtered/sorted by the caller; clicking a row expands the pair-detail
// panel in a full-width row directly below it (single-open). Selection syncs
// to ?pair=c1|c2 by the caller; Esc closes.

import { Fragment, useEffect } from "react";
import type {
  ConceptDict,
  ConfirmationRow,
  District,
  DistrictValue,
  Ego,
  MeasureDict,
} from "@/lib/bundle";
import { fmtInt, fmtMed } from "@/lib/format";
import { RhoPill } from "@/components/rho-pill";
import { DirBadge } from "@/components/dir-badge";
import { PairDetailPanel } from "@/components/pair-detail";

export type SortKey = "l1" | "l2" | "na" | "np" | "med" | "dir" | "rho" | "check";

export const NUM_KEYS: SortKey[] = ["na", "np", "med", "dir", "rho"];

const COLS: [SortKey, string][] = [
  ["l1", "Concept 1"],
  ["l2", "Concept 2"],
  ["na", "Assoc"],
  ["np", "Studies"],
  ["med", "Median effect"],
  ["dir", "SPG direction"],
  ["rho", "City ρ (UHF42)"],
  ["check", "City check"],
];

const rowKey = (r: ConfirmationRow) => `${r.c1}|${r.c2}`;
const normKey = (k: string) => k.split("|").sort().join("|");

export function PairTable({
  rows,
  sort,
  onSort,
  selKey,
  onOpen,
  onClose,
  concepts,
  measures,
  egos,
  districts,
  values,
}: {
  rows: ConfirmationRow[];
  sort: { k: SortKey; dir: number };
  onSort: (k: SortKey) => void;
  /** the open pair as "c1|c2" (either order), or null */
  selKey: string | null;
  onOpen: (r: ConfirmationRow) => void;
  onClose: () => void;
  concepts: ConceptDict;
  measures: MeasureDict;
  egos: Record<string, Ego>;
  districts: District[];
  values: Record<string, Record<string, DistrictValue>>;
}) {
  const mlabel = (mid: string) => measures[mid]?.l ?? mid;
  const label = (cid: string) => concepts[cid]?.l || cid;
  const domShort = (cid: string) => (concepts[cid]?.dm || "beyond-473").split("; ")[0];

  // Esc closes the popup
  useEffect(() => {
    if (!selKey) return;
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [selKey, onClose]);

  // keep the open row in view (deep links land far down the table)
  useEffect(() => {
    if (!selKey) return;
    document.getElementById(`pair-row:${normKey(selKey)}`)?.scrollIntoView({ block: "nearest" });
  }, [selKey]);

  const selPair = selKey
    ? rows.find((r) => normKey(rowKey(r)) === normKey(selKey)) ?? null
    : null;
  const selNorm = selKey ? normKey(selKey) : null;

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="dash-table">
        <thead>
          <tr>
            {COLS.map(([k, t]) => (
              <th
                key={k}
                className={`sortable ${NUM_KEYS.includes(k) ? "num" : ""} ${
                  sort.k === k ? "sorted" : ""
                } ${sort.k === k && sort.dir === 1 ? "asc" : ""}`}
                onClick={() => onSort(k)}
                aria-sort={
                  sort.k === k ? (sort.dir === 1 ? "ascending" : "descending") : undefined
                }
              >
                {t}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const isOpen = selNorm !== null && normKey(rowKey(r)) === selNorm;
            const open = () => onOpen(r);
            return (
              <Fragment key={rowKey(r)}>
                <tr
                  id={`pair-row:${normKey(rowKey(r))}`}
                  className={`rowlink ${isOpen ? "rowopen" : ""}`}
                  tabIndex={0}
                  aria-expanded={isOpen}
                  onClick={open}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") open();
                  }}
                >
                  <td>
                    {label(r.c1)}
                    <span className="dom-note">{domShort(r.c1)}</span>
                  </td>
                  <td>
                    {label(r.c2)}
                    <span className="dom-note">{domShort(r.c2)}</span>
                  </td>
                  <td className="num">{fmtInt(r.na)}</td>
                  <td className="num">{fmtInt(r.np)}</td>
                  <td className="num">{fmtMed(r.med)}</td>
                  <td>
                    <DirBadge dir={r.dir} nsigns={r.nsigns} />
                  </td>
                  <td className="num">
                    <RhoPill rho={r.rho} mod={r.mod} digits={3} />
                  </td>
                  <td>
                    {r.chk ? (
                      r.chk.map(mlabel).join(" + ")
                    ) : (
                      <span className="badge-gray">no district check</span>
                    )}
                  </td>
                </tr>
                {isOpen && selPair && (
                  <tr className="detail-row">
                    <td colSpan={COLS.length}>
                      <PairDetailPanel
                        pair={selPair}
                        concepts={concepts}
                        measures={measures}
                        egos={egos}
                        districts={districts}
                        values={values}
                        onClose={onClose}
                      />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
