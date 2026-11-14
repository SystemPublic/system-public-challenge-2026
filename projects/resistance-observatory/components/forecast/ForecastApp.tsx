"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { AlertFeed } from "@/lib/forecast/types";
import {
  MAX_YEAR,
  MIN_YEAR,
  genomeChangesInYear,
  papersCountsByCountry,
  papersTotals,
} from "@/lib/forecast/data";
import { useForecastUrl } from "@/lib/forecast/url";
import { WorldMap } from "./WorldMap";
import { LegendStrip } from "./Legend";
import { SearchBox } from "./SearchBox";
import { CountryPanel } from "./CountryPanel";
import { TimeControl } from "./TimeControl";
import { WhatMoved } from "./WhatMoved";
import type { SearchResult } from "@/lib/forecast/search";

const PANEL_PX = 420;
const LEFT_PX = 376; // left column (360px) plus its 16px inset
const TOP_PX = 170; // the time control at the top centre
const ZOOM_COL_PX = 16 + 70 + 12; // zoom buttons column plus gaps

export function ForecastApp({ alertFeed }: { alertFeed: AlertFeed }) {
  const {
    country,
    asOfYear,
    layer,
    setLayer,
    setCountry,
    setAsOfYear,
    flushYear,
    hrefForAlert,
    hrefForAlertTab,
  } = useForecastUrl();
  const totals = useMemo(() => papersTotals(asOfYear), [asOfYear]);
  const paperMax = useMemo(
    () => Object.values(papersCountsByCountry(asOfYear)).reduce((m, r) => Math.max(m, r.total), 0),
    [asOfYear],
  );
  const rootRef = useRef<HTMLDivElement>(null);
  const [stageW, setStageW] = useState(1440);
  const [flyKey, setFlyKey] = useState(0);
  const stripRef = useRef<HTMLDivElement>(null);
  const headRef = useRef<HTMLDivElement>(null);
  const [headH, setHeadH] = useState(260);
  const [stripH, setStripH] = useState(110);
  // City name from a city search: UI state only, valid while that country stays selected.
  const [city, setCity] = useState<{ iso3: string; name: string } | null>(null);

  useLayoutEffect(() => {
    const measure = () => {
      if (rootRef.current) setStageW(rootRef.current.getBoundingClientRect().width);
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  // The header card's height: WHAT MOVED starts right under it. (The two are
  // separate in the DOM so the tab order runs search -> date -> what moved.)
  useLayoutEffect(() => {
    const el = headRef.current;
    if (!el) return;
    const measure = () => setHeadH(Math.round(el.getBoundingClientRect().height));
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // The legend strip's height: the fly-to keeps the selected country above it.
  useLayoutEffect(() => {
    const el = stripRef.current;
    if (!el) return;
    const measure = () => setStripH(Math.round(el.getBoundingClientRect().height));
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const markedYears = useMemo(() => {
    const ys = new Set<number>();
    for (let y = MIN_YEAR; y <= MAX_YEAR; y++) if (genomeChangesInYear(y).length > 0) ys.add(y);
    for (const a of alertFeed.alerts) ys.add(a.year);
    return [...ys].sort((a, b) => a - b);
  }, [alertFeed]);

  const selectFromList = useCallback(
    (iso3: string, cityName: string | null) => {
      setCity(cityName ? { iso3, name: cityName } : null);
      setFlyKey((k) => k + 1);
      if (iso3 !== country) setCountry(iso3);
    },
    [country, setCountry],
  );

  const onSearch = useCallback(
    (r: SearchResult) => selectFromList(r.iso3, r.kind === "city" ? r.cityName : null),
    [selectFromList],
  );
  const onMovedSelect = useCallback((iso3: string) => selectFromList(iso3, null), [selectFromList]);

  const onMapSelect = useCallback(
    (iso3: string) => {
      setCity(null);
      if (iso3 !== country) setCountry(iso3);
    },
    [country, setCountry],
  );

  const onClose = useCallback(() => {
    setCity(null);
    setCountry(null);
  }, [setCountry]);

  useEffect(() => {
    if (!country) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !(e.target as HTMLElement)?.closest?.("input,[role=combobox]")) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [country, onClose]);

  const panelPx = country ? Math.min(PANEL_PX, stageW) : 0;
  const leftPx = stageW > 900 ? LEFT_PX : 0;
  const resolvedFromCity = city && city.iso3 === country ? city.name : null;

  return (
    <div ref={rootRef} className="fc-root">
      <div className="fc-stage">
        <h1 className="sr-only">
          Forecast: K540E (pfdhps, sulfadoxine-pyrimethamine) in genome data by country, as of {asOfYear}
        </h1>
        <div ref={headRef} className="fc-card fc-search-card fc-head p-3.5" data-fc-avoid>
          <p className="fc-label">Map · Observed history</p>
          <p className="mt-1 text-[12px] text-muted">
            Observed history only. No projections or future scenarios.
          </p>
          <p className="mt-1.5 text-[13px] leading-snug">
            <span className="font-semibold text-drug">K540E</span> · parasite gene{" "}
            <i>pfdhps</i> · drug: sulfadoxine-pyrimethamine (SP)
          </p>
          <div className="mt-2.5 border-t border-line pt-2">
            <p className="fc-label">Public Graph coverage</p>
            <p className="mt-1 text-[12px] leading-snug tabular-nums">
              The Graph has read {totals.readByGraph} of {totals.total} K540E papers published
              through {asOfYear}.
            </p>
            <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden>
              <div
                className="h-full rounded-full bg-fg"
                style={{ width: `${totals.total > 0 ? (100 * totals.readByGraph) / totals.total : 0}%` }}
              />
            </div>
          </div>
          <SearchBox onSelect={onSearch} className="mt-2.5" />
        </div>

        <div
          data-slot="time-control"
          data-fc-avoid
          onClickCapture={(e) => {
            // Pausing playback: write the shown year to the URL at once.
            const b = (e.target as Element).closest?.("button");
            if (b?.getAttribute("aria-label") === "Pause") setTimeout(flushYear, 0);
          }}
          className="absolute top-4 z-20 -translate-x-1/2"
          style={{ left: `calc(${leftPx}px + (100% - ${leftPx}px - ${panelPx}px) / 2)` }}
        >
          <TimeControl
            year={asOfYear}
            minYear={MIN_YEAR}
            maxYear={MAX_YEAR}
            onChange={setAsOfYear}
            markedYears={markedYears}
          />
        </div>

        <div className="fc-leftcol" data-fc-avoid style={{ top: 16 + headH + 10 }}>
          <WhatMoved
            year={asOfYear}
            alertFeed={alertFeed}
            onSelectCountry={onMovedSelect}
            className="fc-card fc-moved"
          />
        </div>

        <div
          ref={stripRef}
          className="fc-strip"
          data-fc-avoid
          style={{ left: leftPx ? leftPx + 12 : 16, right: panelPx + ZOOM_COL_PX }}
        >
          <LegendStrip
            layer={layer}
            asOfYear={asOfYear}
            placeholder={alertFeed.placeholder}
            paperMax={paperMax}
            wide={stageW - (leftPx ? leftPx + 12 : 16) - panelPx - ZOOM_COL_PX > 900}
            onLayerChange={setLayer}
          />
        </div>

        <WorldMap
          asOfYear={asOfYear}
          selected={country}
          flyKey={flyKey}
          panelPx={panelPx}
          leftPx={leftPx}
          alertFeed={alertFeed}
          layer={layer}
          topPx={TOP_PX}
          bottomPx={stripH + 28}
          onSelect={onMapSelect}
        />

        {country ? (
          <aside className="fc-panel" aria-label="Country evidence" data-fc-avoid>
            <CountryPanel
              key={country}
              iso3={country}
              asOfYear={asOfYear}
              alertFeed={alertFeed}
              resolvedFromCity={resolvedFromCity}
              hrefForAlert={hrefForAlert}
              hrefForAlertTab={hrefForAlertTab}
              onClose={onClose}
            />
          </aside>
        ) : null}
      </div>
    </div>
  );
}
