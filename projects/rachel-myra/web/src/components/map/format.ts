/** "10:54" → "10:54 AM"; "17:30" → "5:30 PM". */
export function clock(hhmm: string | null | undefined): string | null {
  if (!hhmm) return null;
  const m = /^(\d{1,2}):(\d{2})/.exec(hhmm);
  if (!m) return hhmm;
  const h = Number(m[1]);
  const ap = h >= 12 ? "PM" : "AM";
  const h12 = h % 12 === 0 ? 12 : h % 12;
  return `${h12}:${m[2]} ${ap}`;
}

/** 11 → "11 AM", 19 → "7 PM", 0/24 → "midnight". */
export function hourLabel(h: number): string {
  if (h === 0 || h === 24) return "midnight";
  if (h === 12) return "noon";
  return `${h % 12} ${h < 12 ? "AM" : "PM"}`;
}

export function directionsUrl(from: { lat: number; lon: number } | null, to: { lat: number; lon: number }): string {
  const dest = `${to.lat},${to.lon}`;
  const origin = from ? `&origin=${from.lat},${from.lon}` : "";
  return `https://www.google.com/maps/dir/?api=1${origin}&destination=${dest}&travelmode=walking`;
}

export function boundsOf(pts: { lat: number; lon: number }[]): [[number, number], [number, number]] | null {
  if (!pts.length) return null;
  let a = Infinity, b = Infinity, c = -Infinity, d = -Infinity;
  for (const p of pts) { a = Math.min(a, p.lon); b = Math.min(b, p.lat); c = Math.max(c, p.lon); d = Math.max(d, p.lat); }
  if (a === c && b === d) { a -= 0.003; c += 0.003; b -= 0.003; d += 0.003; }
  return [[a, b], [c, d]];
}
