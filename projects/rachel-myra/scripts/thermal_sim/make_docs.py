"""Generate PARAMETERS.md and lib/thermal/params.ts from params.py.

Run:  cd scripts && uv run --python 3.12 --with numpy,pandas python -m thermal_sim.make_docs
"""
from __future__ import annotations

import json
from pathlib import Path

from .params import (COOLANT, COOLANT_TYPES, ENV_LABELS, ENVIRONMENTS, PACKAGING, PARAMS, flat_values)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MD = HERE / "PARAMETERS.md"
TS = REPO / "lib" / "thermal" / "params.ts"

KIND_NOTE = {
    "handbook": "engineering handbook / textbook value",
    "model": "published empirical model",
    "regulatory": "standard or label definition",
    "assumption": "our assumption",
    "free": "assumption, tuned in VALIDATION.md",
}


def _fmt(x: float) -> str:
    return f"{x:g}"


def write_md() -> None:
    lines = [
        "# thermal_sim parameters",
        "",
        "Generated from `params.py` by `python -m thermal_sim.make_docs`. Do not edit by hand.",
        "",
        "**Kinds:** " + "; ".join(f"`{k}` = {v}" for k, v in KIND_NOTE.items()) + ".",
        "",
        "Handbook and model references are standard texts cited by name from general knowledge; "
        "they were **not re-checked page-by-page in this session**. No journal citation in this table "
        "was invented: where we had no source, the row says `assumption`.",
        "",
    ]
    for sec, d in PARAMS.items():
        lines += [f"## {sec}", "", "| key | value | unit | kind | source | meaning |", "|---|---|---|---|---|---|"]
        for k, p in d.items():
            val = _fmt(p.value) + (f" (prior {_fmt(p.prior)})" if p.prior is not None else "")
            lines.append(f"| `{k}` | {val} | {p.unit} | {p.kind} | {p.source} | {p.desc} |")
        lines.append("")
    lines += ["## coolant (shared)", "", "| key | value | unit | kind | source | meaning |", "|---|---|---|---|---|---|"]
    for k, p in COOLANT.items():
        lines.append(f"| `{k}` | {_fmt(p.value)} | {p.unit} | {p.kind} | {p.source} | {p.desc} |")
    lines.append("")
    for t, d in COOLANT_TYPES.items():
        lines += [f"## coolant type `{t}`", "", "| key | value | unit | kind | source | meaning |", "|---|---|---|---|---|---|"]
        for k, p in d.items():
            lines.append(f"| `{k}` | {_fmt(p.value)} | {p.unit} | {p.kind} | {p.source} | {p.desc} |")
        lines.append("")
    lines += ["## packaging", "",
              "| id | outer L x W x H (m) | R_wall (m2K/W) | solar absorptance | contents (kg x J/kgK) | wall heat capacity (J/m2K) | coolant | sources / assumptions |",
              "|---|---|---|---|---|---|---|---|"]
    for k, p in PACKAGING.items():
        cool = (f"{p.coolant_kg:g} kg {p.coolant_type} from {p.coolant_start_c:g} C, product-coolant {p.coolant_G_W_K:g} W/K"
                if p.coolant_kg else "none")
        src = "; ".join(f"{a}: {b}" for a, b in p.sources.items()) or "see poly_mailer for shared contents assumption"
        lines.append(f"| `{k}` | {p.L:g} x {p.W:g} x {p.H:g} | {p.R_wall:g} | {p.absorptance:g} | "
                     f"{p.contents_kg:g} x {p.contents_c:g} | {p.wall_c_per_area:g} | {cool} | {src} |")
    lines += ["", "## environments", "", "| code | meaning | how it is modeled |", "|---|---|---|"]
    how = {
        "pharmacy": "constant `env.pharmacy_c`, still air, no sun",
        "fridge": "constant `env.fridge_c` (only used as the dispense point of cold-chain drugs)",
        "truck": "cargo air lags `T_out + truck_beta * GHI/1000` with time constant `truck_tau_min`; still air, no sun on the package",
        "hub": "`hub_set_c + hub_f * (lag_hub_tau_h(T_out) + hub_gain_c - hub_set_c)`; still air",
        "porch_shade": "outdoor air, porch-level wind, `shade_diffuse_factor` of diffuse light, floor at air temperature",
        "porch_sun": "outdoor air, porch-level wind, beam + diffuse + ground-reflected sun on top and (random-azimuth) sides, long-wave sky loss on top, bottom on a sun-heated floor",
        "mailbox_sun": "steel shell node heated by sun and cooled by wind; package inside sees the shell temperature through still air",
        "lobby": "constant `env.lobby_c` (conditioned lobby, package room or locker)",
        "home_ac": "`min(home_ac_set_c, no-AC temperature)`",
        "home_noac": "`lag_home_tau_h(T_out) + home_gain_c`",
        "home_noac_top": "no-AC temperature + `home_topfloor_c`",
    }
    for e in ENVIRONMENTS:
        lines.append(f"| `{e}` | {ENV_LABELS[e]} | {how[e]} |")
    lines.append("")
    MD.write_text("\n".join(lines))


def write_ts() -> None:
    pk = {k: {"id": p.id, "label": p.label, "L": p.L, "W": p.W, "H": p.H, "R_wall": p.R_wall,
              "absorptance": p.absorptance, "contents_kg": p.contents_kg, "contents_c": p.contents_c,
              "coolant_kg": p.coolant_kg, "coolant_start_c": p.coolant_start_c, "coolant_type": p.coolant_type, "coolant_G_W_K": p.coolant_G_W_K,
              "wall_c_per_area": p.wall_c_per_area} for k, p in PACKAGING.items()}
    vals = flat_values()
    body = [
        "// GENERATED by scripts/thermal_sim/make_docs.py from scripts/thermal_sim/params.py. Do not edit.",
        "// Units and sources: scripts/thermal_sim/PARAMETERS.md",
        "",
        "export type Packaging = {",
        "  id: string; label: string; L: number; W: number; H: number; R_wall: number; absorptance: number;",
        "  contents_kg: number; contents_c: number; coolant_kg: number; coolant_start_c: number;",
        "  coolant_type: string; coolant_G_W_K: number; wall_c_per_area: number;",
        "};",
        "",
        f"export const PARAMS = {json.dumps(vals, indent=2)};",
        "",
        f"export const PACKAGING: Record<string, Packaging> = {json.dumps(pk, indent=2)};",
        "",
        f"export const ENVIRONMENTS = {json.dumps(ENVIRONMENTS)} as const;",
        "export type EnvName = (typeof ENVIRONMENTS)[number];",
        "",
        f"export const ENV_LABELS: Record<string, string> = {json.dumps(ENV_LABELS, indent=2)};",
        "",
    ]
    TS.parent.mkdir(parents=True, exist_ok=True)
    TS.write_text("\n".join(body))


if __name__ == "__main__":
    write_md()
    write_ts()
    print("wrote", MD, "and", TS)
