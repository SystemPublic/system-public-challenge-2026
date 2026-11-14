"use client";
// Client view for the patient "where to go" map. Pass `data` (from getPatientPlanMapData, server side)
// or just `patientId` (it then fetches /api/map/plan?id=...).
import { useEffect, useMemo, useState } from "react";
import { LineLayer, PathLayer, ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import { HELP_HEX, HELP_RGB } from "./colors";
import { boundsOf, clock, directionsUrl } from "./format";
import MapCanvas from "./MapCanvas";
import type { PatientPlanMapData } from "./patientPlanData";
import { PLAN_MAP_STRINGS, type PlanMapLang } from "./planMapStrings";
import { ThreeDToggle } from "./ThreeDToggle";

type CoolRoute = { ok: boolean; chosen: { geometry: { coordinates: number[][] }; distanceM: number; walkMin: number; exposureScore: number }; alternatives: number; steps: { instruction: string; distanceM: number }[] };

const INK: [number, number, number] = [20, 20, 20];

function cleanName(n: string) {
  return n.replace(/\s*-\s*OLDER ADULTS ONLY/i, "").replace(/\s*\(OAC\)/i, "").replace(/\s+OAC$/i, "").trim();
}
function shortName(n: string, max = 28) {
  const s = cleanName(n);
  if (s.length <= max) return s;
  // Cut on a word boundary so big map labels stay readable on a small phone.
  const cut = s.slice(0, max - 1);
  const sp = cut.lastIndexOf(" ");
  return `${sp > 8 ? cut.slice(0, sp) : cut}…`;
}
function titleCase(s: string) {
  return s.toLowerCase().replace(/\b([a-z])/g, (c) => c.toUpperCase());
}

export function PatientPlanMapView({ data: initial, patientId, height = 320, lang = "en", variant = "full" }: { data?: PatientPlanMapData; patientId?: string; height?: number; lang?: PlanMapLang; variant?: "full" | "patient" }) {
  const simple = variant === "patient";
  const t = PLAN_MAP_STRINGS[lang];
  const [data, setData] = useState<PatientPlanMapData | null>(initial ?? null);
  const [err, setErr] = useState(false);
  const [threeD, setThreeD] = useState(false);
  const [cool, setCool] = useState<CoolRoute | null>(null);

  useEffect(() => {
    if (initial || !patientId) return;
    let live = true;
    fetch(`/api/map/plan?id=${encodeURIComponent(patientId)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d: PatientPlanMapData) => { if (live) setData(d); })
      .catch(() => { if (live) setErr(true); });
    return () => { live = false; };
  }, [initial, patientId]);

  const from = data?.home ? `${data.home.lon},${data.home.lat}` : null;
  const to = data?.place ? `${data.place.lon},${data.place.lat}` : null;
  useEffect(() => {
    if (!simple || !from || !to) return;
    let live = true;
    fetch(`/api/route/cool?from=${from}&to=${to}`)
      .then((r) => r.json())
      .then((d: CoolRoute) => { if (live && d?.ok && d.chosen?.geometry?.coordinates?.length) setCool(d); })
      .catch(() => {});
    return () => { live = false; };
  }, [simple, from, to]);

  const layers = useMemo(() => {
    if (!data?.home) return [];
    const home = data.home, place = data.place, sub = simple ? null : data.subway;
    // Patient view: the home label sits below its dot and the place label above, so they don't collide.
    const labels: { pos: [number, number]; text: string; color: [number, number, number]; dy: number }[] = [
      { pos: [home.lon, home.lat], text: simple ? t.you : t.home, color: INK, dy: -26 },
    ];
    if (place) labels.push({ pos: [place.lon, place.lat], text: shortName(titleCase(place.name), simple ? 20 : 28), color: [0, 105, 76], dy: simple ? -28 : -24 });
    if (sub) labels.push({ pos: [sub.lon, sub.lat], text: t.subwayLabel(sub.name), color: INK, dy: -24 });
    return [
      place && cool && new PathLayer({
        id: "cool-route", data: [cool.chosen.geometry.coordinates], parameters: { depthCompare: "always" as const, depthWriteEnabled: false },
        getPath: (d: number[][]) => d as [number, number][], getColor: [20, 20, 20, 210], getWidth: 6, widthUnits: "pixels", capRounded: true, jointRounded: true,
      }),
      place && !cool && new LineLayer({
        id: "route", data: [{ from: [home.lon, home.lat], to: [place.lon, place.lat] }], parameters: { depthCompare: "always" as const, depthWriteEnabled: false },
        getSourcePosition: (d: { from: [number, number] }) => d.from, getTargetPosition: (d: { to: [number, number] }) => d.to,
        getColor: [20, 20, 20, 200], getWidth: simple ? 5 : 4, widthUnits: "pixels",
      }),
      sub && new ScatterplotLayer({
        id: "subway", data: [sub], billboard: true, parameters: { depthCompare: "always" as const, depthWriteEnabled: false }, getPosition: (d: { lon: number; lat: number }) => [d.lon, d.lat],
        getRadius: 7, radiusUnits: "pixels", getFillColor: [255, 255, 255], stroked: true, getLineColor: INK, lineWidthUnits: "pixels", getLineWidth: 3,
      }),
      place && new ScatterplotLayer({
        id: "place", data: [place], billboard: true, parameters: { depthCompare: "always" as const, depthWriteEnabled: false }, getPosition: (d: { lon: number; lat: number }) => [d.lon, d.lat],
        getRadius: simple ? 14 : 11, radiusUnits: "pixels", getFillColor: HELP_RGB, stroked: true, getLineColor: [255, 255, 255], lineWidthUnits: "pixels", getLineWidth: 3,
      }),
      new ScatterplotLayer({
        id: "home", data: [home], billboard: true, parameters: { depthCompare: "always" as const, depthWriteEnabled: false }, getPosition: (d: { lon: number; lat: number }) => [d.lon, d.lat],
        getRadius: 11, radiusUnits: "pixels", getFillColor: INK, stroked: true, getLineColor: [255, 255, 255], lineWidthUnits: "pixels", getLineWidth: 3,
      }),
      new TextLayer({
        id: "labels", data: labels, parameters: { depthCompare: "always" as const, depthWriteEnabled: false }, getPosition: (d) => d.pos, getText: (d) => d.text, getColor: (d) => d.color,
        getSize: simple ? 19 : 15, sizeUnits: "pixels", getPixelOffset: (d) => [0, d.dy], fontWeight: 700, fontFamily: "system-ui, sans-serif",
        background: true, getBackgroundColor: [255, 255, 255, 235], backgroundPadding: simple ? [6, 3] : [4, 2],
        characterSet: "auto",
      }),
    ].filter(Boolean);
  }, [data, t, simple, cool]);

  const fit = useMemo(() => {
    if (!data?.home) return null;
    return boundsOf([data.home, ...(data.place ? [data.place] : []), ...(data.subway && !simple ? [data.subway] : [])]);
  }, [data, simple]);

  if (err) return <p className="rounded-xl bg-[var(--ui-surface,#f7f7f5)] p-4 text-base">{t.loadError}</p>;
  if (!data) return <div style={{ height }} className="rounded-xl bg-[var(--ui-surface,#f7f7f5)] p-4 text-base">{t.loading}</div>;
  if (!data.home) {
    return (
      <p className="rounded-xl border border-dashed p-4 text-sm">
        {t.noHome}
      </p>
    );
  }

  const place = data.place;
  const leave = clock(place?.leaveBy);
  const walk = place?.walkMin != null ? Math.round(place.walkMin) : null;

  if (simple) {
    const opens = clock(place?.opens), closes = clock(place?.closes);
    return (
      <section className="space-y-4 text-[var(--ui-ink,#141414)]" aria-label={t.sectionLabel}>
        <div className="relative overflow-hidden rounded-lg border border-border">
          <MapCanvas
            layers={layers}
            initialView={{ longitude: data.home.lon, latitude: data.home.lat, zoom: 15 }}
            fitBounds={fit}
            threeD={threeD}
            height={height}
            ariaLabel={t.mapAria}
          />
          <div className="absolute left-2 top-2 z-10"><ThreeDToggle on={threeD} onChange={setThreeD} /></div>
        </div>
        {place ? (
          <div className="space-y-2 rounded-lg border border-border bg-card p-4">
            <p className="text-[1.125rem] font-medium text-muted-foreground">{t.goTo}</p>
            <p className="text-[1.75rem] font-semibold leading-tight tracking-tight">{titleCase(cleanName(place.name))}</p>
            <ul className="space-y-1 text-[1.25rem] leading-snug">
              {cool ? <li>{t.walkSidewalks(cool.chosen.walkMin)}</li> : walk !== null && <li>{t.walkShort(walk)}</li>}
              {leave && <li>{t.leaveBy(leave)}</li>}
              {opens && closes && <li>{t.open(opens, closes)}</li>}
            </ul>
            <a
              href={directionsUrl(data.home, place)}
              target="_blank"
              rel="noreferrer"
              className="mt-2 flex min-h-[56px] items-center justify-center rounded-lg bg-primary px-5 text-[1.375rem] font-semibold text-primary-foreground hover:bg-primary/90"
            >
              {t.directions}
            </a>
            {cool && <p className="text-[1rem] text-muted-foreground">{t.coolRouteNote(cool.alternatives)}</p>}
            {cool && cool.steps.length > 0 && (
              <details className="rounded-lg border border-border p-3">
                <summary className="cursor-pointer text-[1.25rem] font-semibold">{t.stepsTitle}</summary>
                <ol className="mt-2 list-decimal space-y-2 pl-6 text-[1.25rem] leading-snug">
                  {cool.steps.map((s, i) => <li key={i}>{s.instruction}</li>)}
                </ol>
              </details>
            )}
            {place.phone && (
              <p className="text-[1.125rem]">
                {t.callFirst} <a className="whitespace-nowrap font-semibold underline" href={`tel:${place.phone}`}>{place.phone}</a>
              </p>
            )}
          </div>
        ) : (
          <p className="text-[1.125rem]">{t.noPlace}</p>
        )}
        {data.delivery.show && (
          <details className="rounded-lg border border-border bg-risk-high-tint p-4">
            <summary className="cursor-pointer text-[1.375rem] font-bold">{t.cantGo}</summary>
            <p className="mt-1 text-[1.125rem]">{t.cantGoText}</p>
          </details>
        )}
      </section>
    );
  }

  return (
    <section className="space-y-4 text-[var(--ui-ink,#141414)]" aria-label={t.sectionLabel}>
      {t.note && <p className="text-xs italic text-[var(--ui-ink-muted,#4b5563)]">{t.note}</p>}
      {place ? (
        <div className="space-y-1">
          <p className="text-sm font-semibold uppercase tracking-wide text-[var(--ui-ink-muted,#4b5563)]">{t.nearest}</p>
          <p className="text-2xl font-bold leading-tight">{titleCase(cleanName(place.name))}</p>
          <p className="text-lg">{titleCase(place.address)}</p>
          <div className="flex flex-wrap gap-2 pt-1">
            {walk !== null && (
              <span className="rounded-full border-2 px-3 py-1 text-lg font-semibold" style={{ borderColor: HELP_HEX }}>
                🚶 {t.walk(walk)}
              </span>
            )}
            {leave && (
              <span className="rounded-full bg-[var(--bucket-store-solid,#0e7c86)] px-3 py-1 text-lg font-bold text-white">{t.leaveBy(leave)}</span>
            )}
          </div>
        </div>
      ) : (
        <p className="rounded-xl border border-dashed p-3 text-sm">{t.noPlace}</p>
      )}

      <div className="relative overflow-hidden rounded-2xl border border-[var(--ui-line,#d4d4d0)]">
        <MapCanvas
          layers={layers}
          initialView={{ longitude: data.home.lon, latitude: data.home.lat, zoom: 15 }}
          fitBounds={fit}
          threeD={threeD}
          height={height}
          ariaLabel={t.mapAria}
        />
        <div className="absolute left-3 top-3 z-10"><ThreeDToggle on={threeD} onChange={setThreeD} large /></div>
      </div>

      <ul className="space-y-2 text-lg">
        {data.hottest && (
          <li>
            <strong>{t.hottestLabel}</strong> {t.hottest(data.hottest.startHour, data.hottest.endHour)}
          </li>
        )}
        {data.subway && (
          <li>
            <strong>{t.subwayTitle}</strong> {data.subway.name} ({data.subway.routes.split(/[\s,]+/).join(", ")}), {t.subwayAbout(data.subway.meters >= 1000 ? `${(data.subway.meters / 1000).toFixed(1)} km` : `${Math.round(data.subway.meters / 10) * 10} m`)}
          </li>
        )}
        {place?.phone && (
          <li><strong>{t.callAhead}</strong> <a className="underline" href={`tel:${place.phone}`}>{place.phone}</a>. {t.callAheadTail}</li>
        )}
        {place?.notes.some((n) => /older adults only/i.test(n)) && <li>{t.olderAdults}</li>}
        {place?.notes.some((n) => /activated heat days/i.test(n)) && <li>{t.coolingCenter}</li>}
      </ul>

      {place && (
        <a
          href={directionsUrl(data.home, place)}
          target="_blank"
          rel="noreferrer"
          className="block rounded-full px-5 py-3 text-center text-lg font-bold text-white"
          style={{ background: "var(--bucket-store-solid, #0e7c86)" }}
        >
          {t.directions}
        </a>
      )}

      {data.delivery.show ? (
        <div className="rounded-2xl border-2 p-4" style={{ borderColor: "var(--risk-high, #d55e00)", background: "var(--risk-high-tint, #fbe3d6)" }}>
          <p className="text-xl font-bold">{t.deliveryTitle}</p>
          <ul className="mt-1 list-disc pl-5 text-lg">
            {data.delivery.reasons.map((r) => <li key={r}>{t.reason(r)}</li>)}
          </ul>
          <p className="mt-2 text-lg">{t.deliveryText}</p>
        </div>
      ) : (
        data.hottest && (
          <p className="text-lg">{t.ifCantLeave(leave, data.hottest.startHour, data.hottest.endHour)}</p>
        )
      )}
      <p className="text-xs text-[var(--ui-ink-muted,#4b5563)]">
        {t.footnote} {t.sources} {data.sources.join(", ")}.
      </p>
    </section>
  );
}

/** Secondary details for the patient view's "More" disclosure (subway, place notes, delivery reasons, sources). */
export function PatientPlanMore({ data, lang = "en" }: { data: PatientPlanMapData; lang?: PlanMapLang }) {
  const t = PLAN_MAP_STRINGS[lang];
  const place = data.place;
  return (
    <ul className="space-y-2">
      {place && <li>{titleCase(place.address)}</li>}
      {place?.notes.some((n) => /older adults only/i.test(n)) && <li>{t.olderAdults}</li>}
      {place?.notes.some((n) => /activated heat days/i.test(n)) && <li>{t.coolingCenter}</li>}
      {data.subway && (
        <li>
          {t.subwayTitle} {data.subway.name} ({data.subway.routes.split(/[\s,]+/).join(", ")}), {t.subwayAbout(data.subway.meters >= 1000 ? `${(data.subway.meters / 1000).toFixed(1)} km` : `${Math.round(data.subway.meters / 10) * 10} m`)}
        </li>
      )}
      {data.delivery.reasons.map((r) => <li key={r}>{t.reason(r)}</li>)}
      <li>{t.footnote}</li>
      <li>{t.sources} {data.sources.join(", ")}.</li>
    </ul>
  );
}
