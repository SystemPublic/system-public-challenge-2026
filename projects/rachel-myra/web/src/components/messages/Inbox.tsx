"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { GroupChip, type RiskGroup } from "./groups";

interface Summary {
  id: string;
  name: string;
  group: RiskGroup;
  zip: string;
  last: string | null;
  lastText: string | null;
  needsAttention: boolean;
}

const TIME = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" });

export function Inbox() {
  const [rows, setRows] = useState<Summary[] | null>(null);
  const [q, setQ] = useState("");
  const [group, setGroup] = useState<RiskGroup | "All">("All");

  useEffect(() => {
    let alive = true;
    const load = () =>
      fetch("/api/messages", { cache: "no-store" })
        .then((r) => r.json())
        .then((d) => alive && setRows(d.conversations ?? []))
        .catch(() => {});
    load();
    const t = setInterval(load, 2500);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const shown = useMemo(() => {
    const list = (rows ?? []).filter(
      (r) => (group === "All" || r.group === group) && (!q || `${r.name} ${r.id} ${r.zip}`.toLowerCase().includes(q.toLowerCase())),
    );
    // Needs attention first, then most recent activity, then High → Low.
    const rank = { High: 0, Medium: 1, Low: 2 };
    return list.sort(
      (a, b) =>
        Number(b.needsAttention) - Number(a.needsAttention) ||
        (b.last ?? "").localeCompare(a.last ?? "") ||
        rank[a.group] - rank[b.group],
    );
  }, [rows, q, group]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <h1 className="text-2xl font-bold tracking-tight">Messages</h1>
      <p className="mt-1 text-ink-muted">Your conversations with patients. Texts are simulated in this prototype; patients are synthetic.</p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search by name, ID or ZIP"
          className="min-w-0 flex-1 rounded-full border border-line-strong px-4 py-2 text-sm"
          aria-label="Search patients"
        />
        <div className="flex overflow-hidden rounded-full border border-line-strong text-sm" role="group" aria-label="Risk group">
          {(["All", "High", "Medium", "Low"] as const).map((g) => (
            <button
              key={g}
              type="button"
              onClick={() => setGroup(g)}
              aria-pressed={group === g}
              className={`px-3 py-2 ${group === g ? "bg-surface font-semibold" : "hover:bg-surface"}`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {rows == null ? (
        <p className="mt-6 text-ink-muted">Loading…</p>
      ) : (
        <ul className="mt-4 divide-y divide-line overflow-hidden rounded-tile border border-line">
          {shown.map((r) => (
            <li key={r.id}>
              <Link href={`/messages/${r.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-surface">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold">{r.name}</span>
                    <GroupChip group={r.group} />
                    {r.needsAttention && (
                      <span className="rounded-full bg-[#fbe3d6] px-2 py-0.5 text-xs font-semibold text-[#a0410a]">Needs a call</span>
                    )}
                  </div>
                  <p className="mt-0.5 truncate text-sm text-ink-muted">{r.lastText ?? "No messages yet"}</p>
                </div>
                <span className="shrink-0 text-xs text-ink-muted">{r.last ? TIME.format(new Date(r.last)) : ""}</span>
              </Link>
            </li>
          ))}
          {!shown.length && <li className="px-4 py-6 text-center text-ink-muted">No patients match.</li>}
        </ul>
      )}
    </div>
  );
}
