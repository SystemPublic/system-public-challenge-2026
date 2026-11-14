"use client";
// Client-only map canvas: MapLibre (OpenFreeMap positron) + deck.gl overlay.
// Load it through next/dynamic with ssr:false (see MapCanvas.tsx).
import { useCallback, useEffect, useRef, useState } from "react";
import type { Ring } from "@/components/replay/area";
import { Map, NavigationControl, useControl, type MapRef } from "react-map-gl/maplibre";
import { MapboxOverlay, type MapboxOverlayProps } from "@deck.gl/mapbox";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

// See app/api/map/maplibre-gl-worker.mjs/route.ts.
if (typeof window !== "undefined") maplibregl.setWorkerUrl(`${window.location.origin}/api/map/maplibre-gl-worker.mjs`);

export const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const BUILDINGS_ID = "tml-3d-buildings";
// Room for the 2D/3D toggle (top-left), zoom buttons (right) and attribution (bottom).
const FIT_PADDING = { top: 72, bottom: 84, left: 56, right: 64 };

function DeckOverlay(props: MapboxOverlayProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

export interface DeckMapProps {
  layers: MapboxOverlayProps["layers"];
  initialView: { longitude: number; latitude: number; zoom: number };
  /** Fit to these bounds [[minLon,minLat],[maxLon,maxLat]] when they change. */
  fitBounds?: [[number, number], [number, number]] | null;
  threeD: boolean;
  getTooltip?: MapboxOverlayProps["getTooltip"];
  onZoom?: (z: number) => void;
  height: number | string;
  ariaLabel: string;
  /** Area-select mode: dragging draws a box (instead of panning) and reports its 4 ground corners. */
  selecting?: boolean;
  onBox?: (ring: Ring) => void;
}

function setBuildings(map: maplibregl.Map, on: boolean) {
  if (!map.isStyleLoaded() && !map.getSource("openmaptiles")) return;
  if (on && !map.getLayer(BUILDINGS_ID) && map.getSource("openmaptiles")) {
    map.addLayer({
      id: BUILDINGS_ID,
      type: "fill-extrusion",
      source: "openmaptiles",
      "source-layer": "building",
      minzoom: 13,
      paint: {
        "fill-extrusion-color": "#dedcd6",
        "fill-extrusion-height": ["coalesce", ["get", "render_height"], 8],
        "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
        "fill-extrusion-opacity": 0.75,
      },
    });
  }
  if (!on && map.getLayer(BUILDINGS_ID)) map.removeLayer(BUILDINGS_ID);
}

export default function DeckMap({ layers, initialView, fitBounds, threeD, getTooltip, onZoom, height, ariaLabel, selecting = false, onBox }: DeckMapProps) {
  const ref = useRef<MapRef>(null);
  const threeDRef = useRef(threeD);
  const [drag, setDrag] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null);
  const finishDrag = () => {
    if (!drag) return;
    const { x0, y0, x1, y1 } = drag;
    setDrag(null);
    const map = ref.current;
    if (!map || Math.abs(x1 - x0) < 6 || Math.abs(y1 - y0) < 6) return; // a click, not a box
    const [l, r, t, b] = [Math.min(x0, x1), Math.max(x0, x1), Math.min(y0, y1), Math.max(y0, y1)];
    const ring: Ring = ([[l, t], [r, t], [r, b], [l, b]] as [number, number][]).map(([x, y]) => {
      const ll = map.unproject([x, y]);
      return [ll.lng, ll.lat];
    });
    onBox?.(ring);
  };

  const apply3D = useCallback((on: boolean) => {
    const m = ref.current?.getMap();
    if (!m) return;
    setBuildings(m, on);
    // Buildings show from zoom 13; zoom in a little so the 3D view has something to show.
    m.easeTo({ pitch: on ? 45 : 0, bearing: on ? -17 : 0, ...(on && m.getZoom() < 14.5 ? { zoom: 14.5 } : {}), duration: 700 });
  }, []);

  useEffect(() => {
    threeDRef.current = threeD;
    apply3D(threeD);
  }, [threeD, apply3D]);

  const firstFit = useRef(true);
  useEffect(() => {
    if (firstFit.current) { firstFit.current = false; return; }
    if (!fitBounds) return;
    ref.current?.fitBounds(fitBounds, { padding: FIT_PADDING, maxZoom: 16, duration: 600 });
  }, [fitBounds]);

  return (
    <div style={{ height, width: "100%", position: "relative" }} role="region" aria-label={ariaLabel}>
      <Map
        ref={ref}
        mapLib={maplibregl}
        initialViewState={
          fitBounds
            ? { bounds: fitBounds, fitBoundsOptions: { padding: FIT_PADDING, maxZoom: 16 }, pitch: 0, bearing: 0 }
            : { ...initialView, pitch: 0, bearing: 0 }
        }
        mapStyle={BASEMAP_STYLE}
        style={{ width: "100%", height: "100%" }}
        maxPitch={60}
        attributionControl={{ compact: true }}
        onLoad={() => { if (threeDRef.current) apply3D(true); onZoom?.(ref.current?.getZoom() ?? initialView.zoom); }}
        onZoomEnd={(e) => onZoom?.(e.viewState.zoom)}
      >
        <NavigationControl position="top-right" visualizePitch />
        <DeckOverlay layers={layers} getTooltip={getTooltip} />
      </Map>
      {/* Area-select overlay: catches the drag so the map doesn't pan, and draws the box. */}
      {selecting && (
        <div
          className="absolute inset-0 z-[5] cursor-crosshair touch-none"
          onPointerDown={(e) => {
            const r = e.currentTarget.getBoundingClientRect();
            e.currentTarget.setPointerCapture(e.pointerId);
            const x = e.clientX - r.left, y = e.clientY - r.top;
            setDrag({ x0: x, y0: y, x1: x, y1: y });
          }}
          onPointerMove={(e) => {
            if (!drag) return;
            const r = e.currentTarget.getBoundingClientRect();
            setDrag({ ...drag, x1: e.clientX - r.left, y1: e.clientY - r.top });
          }}
          onPointerUp={finishDrag}
          onPointerCancel={() => setDrag(null)}
        >
          {drag && (
            <div
              className="pointer-events-none absolute border-2 border-dashed"
              style={{
                left: Math.min(drag.x0, drag.x1),
                top: Math.min(drag.y0, drag.y1),
                width: Math.abs(drag.x1 - drag.x0),
                height: Math.abs(drag.y1 - drag.y0),
                borderColor: "#3730a3",
                background: "rgba(55, 48, 163, 0.1)",
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}
