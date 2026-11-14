"use client";
// Clinician heat + help map (/map): neighborhoods shaded by heat, help places, synthetic patients
// colored by risk group. Click a dot, a place or a neighborhood for a card.
import { useEffect, useMemo, useState } from "react";
import { GeoJsonLayer, IconLayer, PolygonLayer, ScatterplotLayer } from "@deck.gl/layers";
import { inRing, type Ring } from "@/components/replay/area";
import { personIcon } from "./personIcon";
import type { PickingInfo } from "@deck.gl/core";
import { HEAT_HEX, HEAT_RGB, RISK_CSS, RISK_GROUPS, RISK_RGB, type RiskGroup } from "./colors";
import type { HeatArea, HelpPlace, HelpPoint, MapPatient } from "./data";
import { boundsOf, directionsUrl } from "./format";
import { DEFAULT_HELP_TYPES, HELP_FAMILIES, HELP_TYPES, helpFamily } from "./helpTypes";
import MapCanvas from "./MapCanvas";
import { ThreeDToggle } from "./ThreeDToggle";

type Selection =
  | { kind: "patient"; id: string }
  | { kind: "place"; id: string }
  | { kind: "area"; nta: string }
  | { kind: "box" } // everyone inside a box dragged on the map
  | null;

const GROUP_ORDER: Record<RiskGroup, number> = { High: 0, Medium: 1, Low: 2 };

interface Layers {
  heat: { type: "FeatureCollection"; features: HeatArea[] } | null;
  help: HelpPoint[] | null;
  files: { heat: string; help: string };
}

const HEAT_WORDS = ["Among the coolest neighborhoods", "Cooler than most", "In the middle for heat", "Hotter than most", "Among the hottest neighborhoods"];

function GroupChip({ g, children }: { g: RiskGroup; children?: React.ReactNode }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-sm font-semibold"
      style={{ background: RISK_CSS[g].tint, color: RISK_CSS[g].ink, borderColor: RISK_CSS[g].ink }}
    >
      <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: RISK_CSS[g].solid, outline: g === "Medium" ? `1px solid ${RISK_CSS.Medium.ink}` : undefined }} />
      {children ?? g}
    </span>
  );
}

type SendState = { status: "idle" } | { status: "sending" } | { status: "done"; texted: number; calls: number } | { status: "error"; msg: string };

async function send(ps: MapPatient[]): Promise<{ texted: number; calls: number }> {
  const text = ps.filter((p) => p.textOk).map((p) => p.id);
  const call = ps.filter((p) => !p.textOk).map((p) => p.id);
  const post = async (ids: string[], mode: "text" | "call") => {
    if (!ids.length) return 0;
    const r = await fetch("/api/loop/alerts", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ patientIds: ids, mode }) });
    if (!r.ok) throw new Error(`send failed (${r.status})`);
    const j = (await r.json()) as { results?: { ok: boolean }[] };
    return (j.results ?? []).filter((x) => x.ok).length;
  };
  return { texted: await post(text, "text"), calls: await post(call, "call") };
}

function SendButton({ patients, label }: { patients: MapPatient[]; label: string }) {
  const [st, setSt] = useState<SendState>({ status: "idle" });
  const allCall = patients.every((p) => !p.textOk);
  return (
    <div className="space-y-1">
      <button
        type="button"
        disabled={st.status === "sending" || !patients.length}
        onClick={async () => {
          setSt({ status: "sending" });
          try { setSt({ status: "done", ...(await send(patients)) }); } catch (e) { setSt({ status: "error", msg: (e as Error).message }); }
        }}
        className="w-full rounded-full bg-[var(--bucket-store-solid,#0e7c86)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
      >
        {st.status === "sending" ? "Sending…" : allCall && patients.length === 1 ? "Call instead (add to call list)" : label}
      </button>
      {st.status === "done" && (
        <p className="text-sm text-[var(--ui-ink-muted,#4b5563)]" role="status">
          {st.texted > 0 && `Text sent to ${st.texted}. `}
          {st.calls > 0 && `${st.calls} asked not to get texts: added to the call list. `}
          <a className="underline" href="/board">See replies on Patients</a>
        </p>
      )}
      {st.status === "error" && <p className="text-sm text-[var(--risk-high-ink,#a0410a)]">{st.msg}</p>}
    </div>
  );
}

function Card({ title, onClose, children }: { title: React.ReactNode; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="space-y-3 rounded-xl bg-[var(--ui-surface,#f7f7f5)] p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="text-base font-bold leading-snug">{title}</div>
        <button type="button" onClick={onClose} aria-label="Close" className="rounded-full px-2 text-xl leading-none text-[var(--ui-ink-muted,#4b5563)]">×</button>
      </div>
      {children}
    </div>
  );
}

function PatientCard({ p, onClose, backLabel = null, defaultMore = false }: { p: MapPatient; onClose: () => void; backLabel?: string | null; defaultMore?: boolean }) {
  const [more, setMore] = useState(defaultMore);
  return (
    <Card
      title={
        <>
          {backLabel && (
            <button type="button" onClick={onClose} className="mb-2 block text-left text-sm font-semibold text-[var(--layer-graph-fg,#3730a3)] hover:underline">
              ← {backLabel}
            </button>
          )}
          {p.name}
        </>
      }
      onClose={onClose}
    >
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <GroupChip g={p.group}>{p.group} risk</GroupChip>
        <span className="text-[var(--ui-ink-muted,#4b5563)]">Age {p.age}</span>
      </div>
      <p className="text-sm">{p.why}</p>
      <SendButton patients={[p]} label="Text" />
      <button type="button" aria-expanded={more} onClick={() => setMore((v) => !v)} className="text-sm font-semibold underline underline-offset-2">
        {more ? "Less" : "More"}
      </button>
      {more && (
        <div className="space-y-2 text-sm">
          <p className="text-[var(--ui-ink-muted,#4b5563)]">Synthetic patient (not a real person). ZIP {p.zip}.{!p.textOk && " Asked not to get texts: call instead."}</p>
          <p className="font-semibold">Why they are at risk</p>
          <ul className="list-disc space-y-0.5 pl-5">{p.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
          <p>
            <a className="underline" href="/board">Medicines and sources</a> · <a className="underline" href={`/phone/${p.id}`}>Their plan</a>
          </p>
        </div>
      )}
    </Card>
  );
}

function PlaceCard({ id, onClose }: { id: string; onClose: () => void }) {
  const [place, setPlace] = useState<HelpPlace | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let live = true;
    fetch(`/api/map/place?id=${encodeURIComponent(id)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error())))
      .then((d: HelpPlace) => { if (live) { setPlace(d); setErr(false); } })
      .catch(() => { if (live) setErr(true); });
    return () => { live = false; };
  }, [id]);
  if (err) return <Card title="Place" onClose={onClose}><p className="text-sm">Could not load this place.</p></Card>;
  if (!place || place.id !== id) return <Card title="Loading…" onClose={onClose}><span /></Card>;
  const addr = [place.address, place.borough, place.zip].filter(Boolean).join(", ");
  const extra: [string, React.ReactNode][] = [];
  if (place.website) extra.push(["Website", <a key="w" className="break-all underline" href={place.website} target="_blank" rel="noreferrer">{place.website.replace(/^https?:\/\//, "")}</a>]);
  if (place.services) extra.push(["Services", place.services.length > 180 ? `${place.services.slice(0, 177).trimEnd()}…` : place.services]);
  if (place.languages) extra.push(["Languages", place.languages]);
  const fam = HELP_FAMILIES[helpFamily(place.type)];
  return (
    <Card title={place.name} onClose={onClose}>
      <p className="flex items-center gap-2 text-sm text-[var(--ui-ink-muted,#4b5563)]">
        <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: fam.hex }} /> {place.type}
      </p>
      <div className="space-y-0.5 text-sm">
        {addr && <p>{addr}</p>}
        {place.hours && <p>{place.hours}</p>}
        {place.phone && <p><a className="underline" href={`tel:${place.phone}`}>{place.phone}</a></p>}
      </div>
      <a href={directionsUrl(null, place)} target="_blank" rel="noreferrer" className="block rounded-full bg-[var(--bucket-store-solid,#0e7c86)] px-4 py-2 text-center text-sm font-semibold text-white">
        Directions
      </a>
      <p className="text-xs text-[var(--ui-ink-muted,#4b5563)]">Hours and services can change. Call ahead.</p>
      <PlaceMore extra={extra} source={place.source ? `${place.source}${place.accessed ? `, accessed ${place.accessed}` : ""}` : null} />
    </Card>
  );
}

function PlaceMore({ extra, source }: { extra: [string, React.ReactNode][]; source: string | null }) {
  const [more, setMore] = useState(false);
  if (!extra.length && !source) return null;
  return (
    <>
      <button type="button" aria-expanded={more} onClick={() => setMore((v) => !v)} className="text-sm font-semibold underline underline-offset-2">
        {more ? "Less" : "More"}
      </button>
      {more && (
        <dl className="space-y-1.5 text-sm">
          {extra.map(([k, v]) => (
            <div key={k}><dt className="font-semibold">{k}</dt><dd>{v}</dd></div>
          ))}
          {source && <div><dt className="font-semibold">Source</dt><dd className="text-[var(--ui-ink-muted,#4b5563)]">{source}</dd></div>}
        </dl>
      )}
    </>
  );
}

function AreaCard({ area, patients, onPick, onClose }: { area: HeatArea; patients: MapPatient[]; onPick: (id: string) => void; onClose: () => void }) {
  const by = (g: RiskGroup) => patients.filter((p) => p.group === g);
  return (
    <Card title={<>{area.properties.name}<span className="block text-sm font-normal text-[var(--ui-ink-muted,#4b5563)]">{HEAT_WORDS[area.properties.hvi - 1] ?? ""}</span></>} onClose={onClose}>
      {patients.length === 0 ? (
        <p className="text-sm">No patients live here.</p>
      ) : (
        <div className="space-y-3">
          <p className="text-sm">{patients.length} patient{patients.length === 1 ? "" : "s"} live here.</p>
          {RISK_GROUPS.map((g) => {
            const ps = by(g);
            if (!ps.length) return null;
            return (
              <div key={g} className="space-y-2 border-t border-[var(--ui-line,#d4d4d0)] pt-3">
                <GroupChip g={g}>{g} risk · {ps.length}</GroupChip>
                <ul className="max-h-32 space-y-0.5 overflow-auto text-sm">
                  {ps.map((p) => (
                    <li key={p.id}><button type="button" className="text-left underline-offset-2 hover:underline" onClick={() => onPick(p.id)}>{p.name}, {p.age}</button></li>
                  ))}
                </ul>
                <SendButton patients={ps} label={`Text this group (${ps.length})`} />
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

function BoxList({ people, onPick, onClear, onRedo }: { people: MapPatient[]; onPick: (id: string) => void; onClear: () => void; onRedo: () => void }) {
  const counts = { High: 0, Medium: 0, Low: 0 } as Record<RiskGroup, number>;
  for (const p of people) counts[p.group]++;
  return (
    <div className="overflow-hidden rounded-xl border border-[var(--ui-line,#d4d4d0)] bg-white">
      <div className="border-b-4 border-b-[var(--layer-graph-fg,#3730a3)] bg-[var(--layer-graph-bg,#eef2ff)] p-4">
        <div className="flex items-start justify-between gap-2">
          <h2 className="text-base font-bold">
            {people.length} {people.length === 1 ? "person" : "people"} in this area
          </h2>
          <button type="button" onClick={onClear} aria-label="Clear area" className="rounded-full px-2 text-xl leading-none text-[var(--ui-ink-muted,#4b5563)] hover:bg-white">×</button>
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {RISK_GROUPS.map((g) => <GroupChip key={g} g={g}>{counts[g]} {g.toLowerCase()}</GroupChip>)}
        </div>
        <button type="button" onClick={onRedo} className="mt-2 text-sm font-semibold text-[var(--layer-graph-fg,#3730a3)] underline underline-offset-2">
          Select a different area
        </button>
      </div>
      {people.length === 0 ? (
        <p className="p-4 text-sm text-[var(--ui-ink-muted,#4b5563)]">No patients inside this box (with the risk groups that are switched on). Try a bigger area.</p>
      ) : (
        <>
          <ul className="max-h-[44vh] divide-y divide-[var(--ui-line,#d4d4d0)] overflow-y-auto">
            {people.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => onPick(p.id)}
                  className="flex w-full items-start gap-3 border-l-4 px-4 py-2.5 text-left text-sm hover:bg-[var(--ui-surface,#f7f7f5)]"
                  style={{ borderLeftColor: RISK_CSS[p.group].solid }}
                >
                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-x-2">
                      <span className="font-semibold">{p.name}</span>
                      <span className="text-[var(--ui-ink-muted,#4b5563)]">{p.age}</span>
                      <span className="rounded-full px-2 py-px text-xs font-semibold" style={{ background: RISK_CSS[p.group].tint, color: RISK_CSS[p.group].ink }}>{p.group}</span>
                    </span>
                    <span className="mt-0.5 block truncate text-[var(--ui-ink-muted,#4b5563)]">{p.why}</span>
                  </span>
                  <span aria-hidden className="self-center text-[var(--ui-ink-muted,#4b5563)]">›</span>
                </button>
              </li>
            ))}
          </ul>
          <div className="border-t border-[var(--ui-line,#d4d4d0)] p-3">
            <SendButton patients={people} label={`Text everyone in this area (${people.length})`} />
          </div>
        </>
      )}
    </div>
  );
}

export function ClinicianMap({ patients, files, mapHeight = "min(72vh, 760px)" }: { patients: MapPatient[]; files: { panel: string; patients: string }; mapHeight?: string }) {
  const [layers, setLayers] = useState<Layers | null>(null);
  const [loadErr, setLoadErr] = useState(false);
  const [groups, setGroups] = useState<Set<RiskGroup>>(new Set(RISK_GROUPS));
  const [showHeat, setShowHeat] = useState(true);
  const [helpTypes, setHelpTypes] = useState<Set<string>>(new Set(DEFAULT_HELP_TYPES));
  const [threeD, setThreeD] = useState(false);
  const [sel, setSel] = useState<Selection>(null);
  const [zoom, setZoom] = useState(11);
  // Area select: drag a box on the map → everyone inside is listed in the side panel.
  const [selecting, setSelecting] = useState(false);
  const [box, setBox] = useState<Ring | null>(null);
  useEffect(() => {
    if (!selecting) return;
    const k = (e: KeyboardEvent) => e.key === "Escape" && setSelecting(false);
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [selecting]);

  useEffect(() => {
    fetch("/api/map/layers").then((r) => r.json()).then(setLayers).catch(() => setLoadErr(true));
  }, []);

  const counts = useMemo(() => Object.fromEntries(RISK_GROUPS.map((g) => [g, patients.filter((p) => p.group === g).length])) as Record<RiskGroup, number>, [patients]);
  const visiblePatients = useMemo(() => patients.filter((p) => groups.has(p.group)), [patients, groups]);
  const helpVisible = useMemo(() => (layers?.help ?? []).filter((h) => helpTypes.has(h.type)), [layers, helpTypes]);
  const fit = useMemo(() => boundsOf(patients), [patients]);
  const selArea = sel?.kind === "area" ? layers?.heat?.features.find((f) => f.properties.nta === sel.nta) ?? null : null;
  const selPatient = sel?.kind === "patient" ? patients.find((p) => p.id === sel.id) ?? null : null;
  const boxPeople = useMemo(
    () =>
      box
        ? visiblePatients
            .filter((p) => inRing(box, p))
            .sort((a, b) => GROUP_ORDER[a.group] - GROUP_ORDER[b.group] || a.name.localeCompare(b.name))
        : [],
    [box, visiblePatients],
  );

  const deckLayers = useMemo(() => {
    const out = [];
    if (layers?.heat && showHeat) {
      out.push(new GeoJsonLayer<HeatArea["properties"]>({
        id: "heat", data: layers.heat as never, pickable: true, stroked: true, filled: true,
        getFillColor: (f) => [...HEAT_RGB[Math.min(4, Math.max(0, f.properties.hvi - 1))], threeD ? 90 : 140] as [number, number, number, number],
        updateTriggers: { getFillColor: threeD },
        getLineColor: [255, 255, 255, 200], lineWidthUnits: "pixels", getLineWidth: 0.6,
        onClick: (info: PickingInfo) => { const f = info.object as HeatArea | undefined; if (f) setSel({ kind: "area", nta: f.properties.nta }); },
      }));
    }
    if (selArea) {
      out.push(new GeoJsonLayer({
        id: "heat-selected", data: { type: "FeatureCollection", features: [selArea] } as never, filled: false, stroked: true,
        getLineColor: [20, 20, 20, 255], lineWidthUnits: "pixels", getLineWidth: 3,
      }));
    }
    if (box) {
      out.push(new PolygonLayer<Ring>({
        id: "box", data: [box], getPolygon: (r) => [...r, r[0]], filled: true, stroked: true,
        getFillColor: [55, 48, 163, 22], getLineColor: [55, 48, 163, 230], getLineWidth: 2, lineWidthUnits: "pixels", pickable: false,
      }));
    }
    if (layers?.help) {
      // Small, muted dots: one color per family. Patient dots stay bigger and on top.
      const r = zoom >= 14 ? 5 : zoom >= 12.5 ? 3.5 : 2.5;
      out.push(new ScatterplotLayer<HelpPoint>({
        id: "help", data: helpVisible, pickable: true, billboard: true, parameters: { depthCompare: "always" as const, depthWriteEnabled: false },
        getPosition: (d) => [d.lon, d.lat],
        getRadius: r, radiusUnits: "pixels", radiusMinPixels: 2,
        getFillColor: (d) => [...HELP_FAMILIES[helpFamily(d.type)].rgb, 210] as [number, number, number, number],
        stroked: true, lineWidthUnits: "pixels", getLineWidth: 1, getLineColor: [255, 255, 255, 230],
        updateTriggers: { getRadius: r },
        onClick: (info: PickingInfo) => { const d = info.object as HelpPoint | undefined; if (d) setSel({ kind: "place", id: d.id }); },
      }));
    }
    // Patients: a tiny person per home (restroom-sign style), colored by risk group.
    out.push(new IconLayer<MapPatient>({
      id: "patients", data: visiblePatients, pickable: true, billboard: true, parameters: { depthCompare: "always" as const, depthWriteEnabled: false },
      getPosition: (d) => [d.lon, d.lat],
      getIcon: (d) =>
        selPatient?.id === d.id
          ? personIcon(RISK_RGB[d.group].solid, [20, 20, 20], 2)
          // White outline on every group so orange/yellow people stay visible on the heat shading.
          : personIcon(RISK_RGB[d.group].solid, [255, 255, 255], 2.4),
      getSize: (d) => (selPatient?.id === d.id ? 34 : 22), sizeUnits: "pixels",
      // With a box drawn, fade the people outside it.
      getColor: (d) => [255, 255, 255, box && !inRing(box, d) ? 70 : 255] as [number, number, number, number],
      // SVG icons must load as <img> (createImageBitmap can't decode SVG blobs).
      loadOptions: { image: { type: "image" } },
      updateTriggers: { getIcon: selPatient?.id, getSize: selPatient?.id, getColor: box },
      onClick: (info: PickingInfo) => { const d = info.object as MapPatient | undefined; if (d) setSel({ kind: "patient", id: d.id }); },
    }));
    return out;
  }, [layers, showHeat, helpVisible, visiblePatients, selArea, selPatient, zoom, threeD, box]);

  const getTooltip = ({ object, layer }: PickingInfo) => {
    if (!object || !layer) return null;
    if (layer.id === "patients") { const p = object as MapPatient; return { text: `${p.name}: ${p.group} risk` }; }
    if (layer.id === "help") { const h = object as HelpPoint; return { text: `${h.name}\n${h.type}` }; }
    if (layer.id === "heat") { const f = object as HeatArea; return { text: f.properties.name }; }
    return null;
  };

  const areaOptions = useMemo(() => {
    const m = new Map<string, { nta: string; name: string; n: number; high: number }>();
    for (const p of patients) {
      if (!p.nta) continue;
      const o = m.get(p.nta) ?? { nta: p.nta, name: p.ntaName ?? p.nta, n: 0, high: 0 };
      o.n++; if (p.group === "High") o.high++;
      m.set(p.nta, o);
    }
    return [...m.values()].sort((a, b) => b.high - a.high || b.n - a.n);
  }, [patients]);

  const toggle = <T,>(set: Set<T>, v: T) => { const n = new Set(set); if (n.has(v)) n.delete(v); else n.add(v); return n; };
  const areaPatients = selArea ? patients.filter((p) => p.nta === selArea.properties.nta && groups.has(p.group)) : [];
  const mainTypes = HELP_TYPES.filter((t) => t.main);
  const moreTypes = HELP_TYPES.filter((t) => !t.main);
  const moreOn = moreTypes.filter((t) => helpTypes.has(t.type)).length;

  const typeRow = (t: (typeof HELP_TYPES)[number]) => (
    <label key={t.type} className="flex items-center gap-2 py-0.5">
      <input type="checkbox" checked={helpTypes.has(t.type)} onChange={() => setHelpTypes((s) => toggle(s, t.type))} />
      <span aria-hidden className="inline-block h-2 w-2 rounded-full" style={{ background: HELP_FAMILIES[t.family].hex }} />
      <span>{t.label}</span>
    </label>
  );

  const heading = "text-xs font-semibold uppercase tracking-wide text-[var(--ui-ink-muted,#4b5563)]";

  const panel = (
    <div className="space-y-5 text-sm">
      {sel?.kind === "patient" && selPatient && (
        <PatientCard
          key={selPatient.id}
          p={selPatient}
          // Opened with a box drawn: closing goes back to the list, and the full reasons start open.
          onClose={() => setSel(box ? { kind: "box" } : null)}
          backLabel={box ? `Back to the ${boxPeople.length} ${boxPeople.length === 1 ? "person" : "people"} in this area` : null}
          defaultMore={!!box}
        />
      )}
      {sel?.kind === "box" && box && (
        <BoxList
          people={boxPeople}
          onPick={(id) => setSel({ kind: "patient", id })}
          onClear={() => { setBox(null); setSel(null); }}
          onRedo={() => setSelecting(true)}
        />
      )}
      {sel?.kind === "place" && <PlaceCard id={sel.id} onClose={() => setSel(null)} />}
      {selArea && <AreaCard area={selArea} patients={areaPatients} onPick={(id) => setSel({ kind: "patient", id })} onClose={() => setSel(null)} />}

      <section className="space-y-2">
        <h2 className={heading}>Patients</h2>
        <div className="flex flex-wrap gap-2">
          {RISK_GROUPS.map((g) => (
            <button
              key={g}
              type="button"
              aria-pressed={groups.has(g)}
              onClick={() => setGroups((s) => toggle(s, g))}
              className="rounded-full border px-3 py-1 font-semibold transition-opacity"
              style={{ background: groups.has(g) ? RISK_CSS[g].tint : "white", color: RISK_CSS[g].ink, borderColor: RISK_CSS[g].ink, opacity: groups.has(g) ? 1 : 0.5 }}
            >
              <span aria-hidden className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full align-middle" style={{ background: RISK_CSS[g].solid, outline: g === "Medium" ? `1px solid ${RISK_CSS.Medium.ink}` : undefined }} />
              {g} risk · {counts[g]}
            </button>
          ))}
        </div>
        <select
          aria-label="Pick a neighborhood"
          className="w-full rounded-lg border border-[var(--ui-line,#d4d4d0)] bg-white px-2 py-1.5"
          value={selArea?.properties.nta ?? ""}
          onChange={(e) => setSel(e.target.value ? { kind: "area", nta: e.target.value } : null)}
        >
          <option value="">Pick a neighborhood to text a group…</option>
          {areaOptions.map((o) => (
            <option key={o.nta} value={o.nta}>{o.name} ({o.n} patients{o.high ? `, ${o.high} high risk` : ""})</option>
          ))}
        </select>
      </section>

      <section className="space-y-2">
        <h2 className={heading}>Neighborhood heat</h2>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={showHeat} onChange={(e) => setShowHeat(e.target.checked)} />
          <span className="flex flex-1 items-center gap-2 text-[var(--ui-ink-muted,#4b5563)]">
            <span>Cooler</span>
            <span className="h-2.5 flex-1 rounded-full" style={{ background: `linear-gradient(to right, ${HEAT_HEX.join(",")})` }} />
            <span>Hotter</span>
          </span>
        </label>
      </section>

      <section className="space-y-1">
        <h2 className={heading}>Places to cool off</h2>
        <div className="grid">{mainTypes.map(typeRow)}</div>
        <details className="pt-1">
          <summary className="cursor-pointer font-semibold">More places{moreOn ? ` (${moreOn} on)` : ""}</summary>
          <div className="grid pt-1">{moreTypes.map(typeRow)}</div>
        </details>
      </section>

      <details className="border-t border-[var(--ui-line,#d4d4d0)] pt-3 text-xs text-[var(--ui-ink-muted,#4b5563)]">
        <summary className="cursor-pointer font-semibold">Sources</summary>
        <ul className="mt-2 space-y-1">
          <li>Patients are synthetic (no real people): {files.panel}, {files.patients}.</li>
          <li>Neighborhood heat: {layers?.files.heat ?? "data/processed/hvi_nta2020.geojson"} (NYC heat vulnerability index).</li>
          <li>Places: {layers?.files.help ?? "data/processed/community_resources_nyc.geojson"}.</li>
          <li>Basemap © OpenFreeMap, OpenMapTiles, OpenStreetMap contributors.</li>
        </ul>
      </details>
    </div>
  );

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="relative min-w-0 self-start overflow-hidden rounded-xl border border-[var(--ui-line,#d4d4d0)]">
        <MapCanvas
          layers={deckLayers}
          initialView={{ longitude: -73.89, latitude: 40.85, zoom: 11.5 }}
          fitBounds={fit}
          threeD={threeD}
          getTooltip={getTooltip}
          onZoom={setZoom}
          height={mapHeight}
          ariaLabel="Map of synthetic patients, neighborhood heat and places to cool off"
          selecting={selecting}
          onBox={(ring) => { setSelecting(false); setBox(ring); setSel({ kind: "box" }); }}
        />
        {/* Top-right, just left of the zoom buttons. */}
        <button
          type="button"
          onClick={() => setSelecting((s) => !s)}
          aria-pressed={selecting}
          className={`absolute right-12 top-2.5 z-10 rounded-full border-2 border-[var(--layer-graph-fg,#3730a3)] px-3.5 py-1.5 text-sm font-semibold shadow-sm ${
            selecting ? "bg-[var(--layer-graph-fg,#3730a3)] text-white" : "bg-white text-[var(--layer-graph-fg,#3730a3)] hover:bg-[var(--layer-graph-bg,#eef2ff)]"
          }`}
        >
          {selecting ? "Cancel selecting" : "Select an area"}
        </button>
        {selecting && (
          <div className="pointer-events-none absolute bottom-10 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-full bg-[var(--layer-graph-fg,#3730a3)] px-4 py-1.5 text-sm font-semibold text-white shadow">
            Drag a box around the people you want to see · Esc to cancel
          </div>
        )}
        <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
          <ThreeDToggle on={threeD} onChange={setThreeD} />
          {!layers && !loadErr && <span className="rounded-full bg-white px-3 py-1 text-xs shadow-sm">Loading…</span>}
          {loadErr && <span className="rounded-full bg-white px-3 py-1 text-xs shadow-sm">Could not load heat and places.</span>}
        </div>
      </div>
      <aside aria-label="Map details and filters" className="min-w-0">{panel}</aside>
    </div>
  );
}
