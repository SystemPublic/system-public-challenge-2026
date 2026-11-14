"use client";

import { useMemo, useState } from "react";
import { deriveAlerts, type AlertData, type Watch } from "@/lib/alert/derive";
import { composeAlert, composeEmail } from "@/lib/alert/compose";
import { pmidStr, type ClientPack, type MarkerDef, type Paper } from "@/lib/alert/pack";
import { GRAPH_RELEASE, pubmedUrl, type EmailExtras } from "@/lib/alert/receipt";
import type { LiveCoverage, LiveFinding, LivePaper, LiveStudies } from "./useSystem";

/**
 * The demo send: the newest genome cell in the pack (DR Congo, collected 2022)
 * on a "rises to or above 25%" preset watch, packaged with the papers
 * published since, a live System graph check with its quarantine count, and
 * the unread curation queue. Same templates as every other alert email.
 */
export const TEST_ALERT = { area: "COD", trig: "rise", level: 25 } as const;
/** The quarantine example shown on the page: Gutman et al. 2015 and the two association ids the vetted set excludes. */
const QUARANTINE_EXAMPLE = { pmid: "25564249", label: "Gutman et al. 2015, Malawi", ids: ["paFNq6MPX5", "AeI-laBxXr"] } as const;

export const DEMO_EMAIL = process.env.NEXT_PUBLIC_DEMO_EMAIL ?? "";

type State = { s: "idle" } | { s: "working"; step: string } | { s: "sent"; id: string; to: string } | { s: "error"; message: string };

/**
 * One live question. The beta API has transient 5xx spells, and the server caches each
 * upstream call that succeeds, so a retry usually completes what the last attempt began.
 */
async function ask<T>(query: string, tries = 3): Promise<T | null> {
  for (let i = 0; i < tries; i++) {
    try {
      const j = (await (await fetch(`/api/alert/system?${query}`)).json()) as { live?: boolean };
      if (j.live) return j as T;
    } catch {
      /* try again */
    }
    if (i < tries - 1) await new Promise((r) => setTimeout(r, 700));
  }
  return null;
}

export function SendTestAlert({
  pack,
  marker,
  data,
  papers,
  asOfLine,
  configured,
  onJump,
}: {
  pack: ClientPack;
  marker: MarkerDef;
  data: AlertData;
  papers: Map<string, Paper>;
  asOfLine: string;
  configured: boolean | null;
  onJump: (qs: Record<string, string>) => void;
}) {
  const [to, setTo] = useState(DEMO_EMAIL);
  const [state, setState] = useState<State>({ s: "idle" });

  const area = TEST_ALERT.area;
  const info = pack.genomes.countries[area];
  const watch: Watch = useMemo(
    () => ({ marker: marker.key, area, trigger: "rise", level: TEST_ALERT.level, points: pack.thresholds.presets?.change_points ?? 20, minN: pack.thresholds.presets?.min_samples ?? 20 }),
    [marker.key, area, pack.thresholds.presets],
  );
  const event = useMemo(
    () =>
      deriveAlerts(watch, data)
        .filter((e) => e.source === "genomes" && e.fired)
        .at(-1),
    [watch, data],
  );
  if (!info || !event?.cell) return null;
  const e = event;
  const cell = event.cell;
  const country = info.country;
  const qs = { area, trig: TEST_ALERT.trig, level: String(TEST_ALERT.level), finding: e.id };

  async function send(ev: React.FormEvent) {
    ev.preventDefault();
    if (!configured) return;
    onJump(qs);
    try {
      setState({ s: "working", step: "Checking the System API…" });
      const composed = composeAlert({ e, watch, marker, country, basis: info.who_basis, pack, cells: data.cells, papers });

      const unread = pack.literature.papers
        .filter((p) => !p.in_graph && (p.countries_iso3 ?? []).includes(area) && p.pub_year >= cell.year)
        .sort((a, b) => b.pub_year - a.pub_year);
      const unreadIds = unread.map((p) => pmidStr(p.pmid)).filter((id) => /^\d+$/.test(id));
      // coverage first and on its own: it is many upstream calls, and the API dislikes bursts
      const coverage = await ask<LiveCoverage>("op=coverage", 4);
      // then one at a time, for the same reason
      const example = await ask<LivePaper>(`op=paper&pmid=${QUARANTINE_EXAMPLE.pmid}`);
      const held = unreadIds.length ? await ask<LiveStudies>(`op=studies&pmids=${unreadIds.slice(0, 45).join(",")}`) : null;
      const checks: (LiveFinding | null)[] = [];
      for (const id of [...QUARANTINE_EXAMPLE.ids, ...composed.stakes.lead.map((f) => f.system_id)]) checks.push(await ask<LiveFinding>(`op=finding&id=${encodeURIComponent(id)}`));
      const exampleChecks = checks.slice(0, QUARANTINE_EXAMPLE.ids.length);
      const leadChecks = checks.slice(QUARANTINE_EXAMPLE.ids.length);
      const live = Boolean(coverage);

      const liveChecked: Record<string, string> = {};
      composed.stakes.lead.forEach((f, i) => {
        const c = leadChecks[i];
        if (!c) return;
        const v = c.finding?.statistic_value;
        liveChecked[f.system_id] = c.vetted === false ? "API check: id not in the vetted set" : c.finding ? `API check: ${v === f.statistic_value ? "matches snapshot" : "differs from snapshot"}` : "API check: id not returned";
      });

      const graphLive: string[] = [];
      if (coverage) {
        graphLive.push(
          `System API connected, checked just now: ${coverage.total} associations returned across the ${coverage.papers.length} ${marker.mutation} papers the graph has read (${coverage.confirmed} confirmed live): ${coverage.shown} vetted, ${coverage.quarantined} unvetted and quarantined. Quarantined associations are counted, never shown.`,
        );
      } else {
        graphLive.push(`System API not connected just now; the graph details in this email are from the data pack (${GRAPH_RELEASE}).`);
      }
      const quarantinedIds = QUARANTINE_EXAMPLE.ids.filter((_, i) => exampleChecks[i]?.found && exampleChecks[i]?.vetted === false);
      if (example?.inGraph && quarantinedIds.length) {
        graphLive.push(
          `Quarantine example, ${QUARANTINE_EXAMPLE.label} (PMID ${QUARANTINE_EXAMPLE.pmid}): the System API returns ${example.total} association${example.total === 1 ? "" : "s"} for this paper, ${example.quarantined} outside the vetted set, including ${quarantinedIds.join(" and ")}. The extractor attached risks reported for the A581G-bearing sextuple haplotype to ${marker.mutation}; they are not shown as evidence about ${marker.mutation}.`,
        );
      }

      const figures = pack.literature.abstract_prevalence.filter((f) => f.iso3 === area && f.pub_year >= cell.year).sort((a, b) => b.pub_year - a.pub_year);
      const nowHeld = held ? new Set(held.held.map((h) => h.pmid)) : null;
      const extras: EmailExtras = {
        subjectTag: live ? "System API connected" : "System graph v2.1 snapshot",
        liveChecked,
        graphLive,
        recent: {
          title: `Papers published since the ${cell.year} collection that state a ${marker.mutation} figure for ${country}:`,
          items: figures.map((f) => {
            const id = pmidStr(f.pmid);
            const window = f.year_start ? `samples from ${f.year_start}${f.year_end && f.year_end !== f.year_start ? ` to ${f.year_end}` : ""}` : "collection years not stated";
            return {
              text: `Published ${f.pub_year}: “${f.quote}” · ${f.site ? `site: ${f.site}` : "no single site stated"} · ${window}${f.population ? ` · population: ${f.population}` : ""} · ${papers.get(id)?.title ?? "title not recorded"}`,
              link: { label: `PMID ${id}`, url: papers.get(id)?.url ?? pubmedUrl(id) },
            };
          }),
          note: `Published Molecular / Clinical Papers: machine-read abstracts, quoted word for word, not checked by hand. They sit beside the ${composed.ctx?.geo?.site ? `single-site ${composed.ctx.geo.site} ` : ""}genome count and are never pooled with it: different designs, places and years.`,
        },
        queue: {
          title: `${marker.mutation} papers naming ${country}, published since ${cell.year}, that the graph has not read (snapshot)${nowHeld ? `; per the API the graph now holds ${unreadIds.filter((id) => nowHeld.has(id)).length} of ${unreadIds.length}` : ""}:`,
          items: unread.slice(0, 6).map((p) => {
            const id = pmidStr(p.pmid);
            return { text: `Published ${p.pub_year}: ${p.title}${nowHeld?.has(id) ? " (now in the graph, per the API)" : ""}`, link: { label: `PMID ${id}`, url: p.url ?? pubmedUrl(id) } };
          }),
        },
        links: [{ label: "See this country on the Forecast map", url: `${window.location.origin}/forecast?country=${area}&marker=${encodeURIComponent(marker.urlId)}` }],
      };

      const q = new URLSearchParams({ marker: marker.urlId, ...qs });
      const email = composeEmail(composed, { e, watch, marker, country, link: `${window.location.origin}/alert?${q.toString()}`, asOf: asOfLine, extras });

      setState({ s: "working", step: "Sending…" });
      const res = await fetch("/api/alert/email", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ to: to.trim(), subject: email.subject, text: email.text, html: email.html }) });
      const json = (await res.json()) as { ok?: boolean; id?: string; error?: string; to?: string };
      if (json.ok && json.id) setState({ s: "sent", id: json.id, to: json.to ?? to });
      else setState({ s: "error", message: json.error ?? `HTTP ${res.status}` });
    } catch (err) {
      setState({ s: "error", message: err instanceof Error ? err.message : String(err) });
    }
    setTimeout(() => document.getElementById("alert-detail")?.scrollIntoView({ block: "start", behavior: "smooth" }), 300);
  }

  const busy = state.s === "working";
  return (
    <section aria-labelledby="test-h" className="mb-5 rounded-[var(--radius)] border border-signal/50 bg-signal-soft/30 p-4">
      <form onSubmit={send} className="flex flex-wrap items-center gap-x-4 gap-y-3">
        <div className="min-w-[16rem] flex-1">
          <h2 id="test-h" className="font-mono text-xs uppercase tracking-[0.18em] text-signal">
            Send a test alert
          </h2>
          <p className="mt-1 text-sm">
            The newest genome cell in the record: <strong>{country}</strong>, collected {cell.year}, {cell.x} of {cell.n} samples carrying {marker.label} ({cell.pct.toFixed(1)}%), on a “rises to or
            above {TEST_ALERT.level}%” preset watch for {marker.drugShort}.{" "}
            <button type="button" onClick={() => onJump(qs)} className="text-drug underline underline-offset-2">
              Open it
            </button>
          </p>
        </div>
        <label className="sr-only" htmlFor="test-alert-to">
          Recipient email address
        </label>
        <input
          id="test-alert-to"
          type="email"
          required
          value={to}
          onChange={(x) => setTo(x.target.value)}
          placeholder="you@institute.org"
          disabled={!configured}
          className="h-10 w-64 min-w-0 rounded-full border border-line-strong bg-surface px-3.5 text-sm disabled:opacity-50"
        />
        <button type="submit" disabled={!configured || busy} className="h-10 rounded-full bg-signal px-5 text-sm font-semibold text-bg disabled:opacity-40">
          {configured === null ? "Checking…" : !configured ? "Preview only" : busy ? "Sending…" : "Send Test Alert"}
        </button>
      </form>
      <p className="mt-2 text-xs text-muted" aria-live="polite">
        {state.s === "sent" ? (
          <span className="text-drug">
            ✓ Sent · Resend ID <span className="font-mono">{state.id}</span> · to {state.to}
          </span>
        ) : state.s === "error" ? (
          <span className="text-signal">Not sent. The provider said: “{state.message}”</span>
        ) : state.s === "working" ? (
          state.step
        ) : configured === false ? (
          "No email key is configured on this server, so nothing can be sent. Open the alert to preview the email."
        ) : (
          "One email: the count beside the watch cutoff, the study behind it, papers published since, a System API check with its quarantine count, the curation queue, and the receipt. A replay of the historical record, not live surveillance."
        )}
      </p>
    </section>
  );
}
