// Plain-language version of the pipeline's readiness drivers (same facts, simpler words). Pure.
export function plainWhy(d: string): string {
  const s = d.trim();
  let m = /^neighborhood heat vulnerability index (\d)( \(highest\))?$/.exec(s);
  if (m) return Number(m[1]) >= 4 ? "lives in one of the most heat-vulnerable neighborhoods" : "neighborhood is somewhat heat-vulnerable";
  m = /^lives on floor (\d+) or higher$/.exec(s);
  if (m) return `lives on floor ${m[1]} or higher`;
  m = /^floor (\d+)\+ with no elevator$/.exec(s);
  if (m) return `lives on floor ${m[1]}+ with no elevator`;
  m = /^age (\d+)\+$/.exec(s);
  if (m) return `${m[1]} or older`;
  m = /^on (.+)$/.exec(s);
  if (m) return `takes ${m[1].replace(/ \+ /g, " and ")}`;
  const map: Record<string, string> = {
    "no working ac at home": "no working AC at home",
    "has ac but cost limits use": "has AC but cost limits use",
    "home all day without reliable ac": "home all day without reliable AC",
    "can reach a cool place only with help": "needs help to get to a cool place",
    "cannot get to a cool place": "can't get to a cool place",
    "spends the day outdoors or doing physical work": "outdoors or doing physical work during the day",
    "uses power-dependent equipment": "uses equipment that needs power",
  };
  return map[s] ?? s;
}
