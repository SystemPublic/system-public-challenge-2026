// Tidy raw (often ALL-CAPS) place names and addresses from city open data for display.
// - ALL-CAPS words become Title Case; known acronyms stay upper case.
// - Words that were already mixed case are left alone.
// - Trailing tags like " -OLDER ADULTS ONLY" are dropped from names (see placeNote).

const ACRONYMS = new Set([
  "OAC", "NYC", "NYCHA", "YMCA", "YWCA", "SAGE", "NYPL", "BPL", "QPL", "PS", "IS", "HS", "MS", "CUNY", "II", "III", "IV",
  "NE", "NW", "SE", "SW",
]);

const OLDER_ADULTS_RE = /\s*[-–—]\s*older\s+adults?\s+only\s*$/i;

function tidyWord(w: string): string {
  // Only touch words that are entirely upper case (letters), e.g. "PROSPECT", "AVE.", "ST'S".
  if (!/[A-Z]/.test(w) || /[a-z]/.test(w)) return w;
  const core = w.replace(/[^A-Z0-9]/g, "");
  if (ACRONYMS.has(core)) return w;
  // Ordinals like "1ST", "42ND" -> "1st", "42nd".
  if (/^\d+(ST|ND|RD|TH)$/.test(core)) return w.toLowerCase();
  return w.toLowerCase().replace(/(^|[^a-z'])([a-z])/g, (_m, pre: string, ch: string) => pre + ch.toUpperCase());
}

function tidyText(s: string): string {
  return s
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .map(tidyWord)
    .join(" ");
}

/** Clean a place name for display ("SAGE Center Bronx at Crotona Pride House OAC"). */
export function tidyPlaceName(name: string | null | undefined): string {
  if (!name) return "";
  return tidyText(name.replace(OLDER_ADULTS_RE, ""));
}

/** Clean a street address for display ("1784 Prospect Avenue"). */
export function tidyAddress(addr: string | null | undefined): string {
  if (!addr) return "";
  return tidyText(addr);
}

/** A short note for facts stripped from the raw name, e.g. "For adults 60+". Null if none. */
export function placeNote(name: string | null | undefined): string | null {
  if (!name) return null;
  return OLDER_ADULTS_RE.test(name) || /older\s+adults?\s+only/i.test(name) ? "For adults 60+" : null;
}
