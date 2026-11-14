"""Single source of truth for every model parameter.

Each entry carries value, unit, a source and a *kind*:

- ``handbook``   : engineering-handbook / textbook value (cited by name; these
                   standard references were cited from general knowledge and
                   were NOT re-checked line-by-line in this session).
- ``model``      : a published, widely implemented empirical model.
- ``regulatory`` : a standard or label definition (USP, prescribing information).
- ``assumption`` : our engineering judgement. Treat as uncertain.
- ``free``       : an assumption that the validation step is allowed to tune
                   (see VALIDATION.md). Its prior value is kept in ``prior``.

``PARAMETERS.md`` is generated from this file (``python -m
thermal_sim.make_docs``) and ``lib/thermal/params.ts`` is generated from it
too, so the Python model, the TypeScript port and the documentation can never
drift apart.  Never edit the generated files by hand.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class P:
    value: float
    unit: str
    kind: str
    source: str
    desc: str
    prior: Optional[float] = None


HANDBOOK_ASHRAE = "ASHRAE Handbook - Fundamentals (surface film / sol-air chapter)"
HANDBOOK_INCROPERA = "Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (property tables)"
DUFFIE = "Duffie & Beckman, Solar Engineering of Thermal Processes"

PARAMS: Dict[str, Dict[str, P]] = {
    # ------------------------------------------------------------------ site
    "site": {
        "lat_deg": P(40.85, "deg N", "assumption", "SBH Health System, Bronx (approx.)", "Latitude used for sun position"),
        "lon_deg": P(-73.89, "deg E", "assumption", "SBH Health System, Bronx (approx.)", "Longitude used for sun position"),
        "utc_offset_h": P(-4.0, "h", "regulatory", "US Eastern Daylight Time", "Fixed local-time offset (summer). Use -5 in winter."),
    },
    # ----------------------------------------------------------------- solar
    "solar": {
        "solar_const": P(1367.0, "W/m2", "handbook", DUFFIE, "Solar constant for extraterrestrial irradiance"),
        "haurwitz_a": P(1098.0, "W/m2", "model", "Haurwitz (1945) clear-sky model, as implemented in pvlib", "GHI_clear = a*cosZ*exp(-b/cosZ)"),
        "haurwitz_b": P(0.057, "-", "model", "Haurwitz (1945) clear-sky model, as implemented in pvlib", "Haurwitz exponent"),
        "kc_a": P(0.75, "-", "model", "Kasten & Czeplak (1980) cloud correction", "GHI = GHI_clear*(1 - a*N^b), N = cloud fraction"),
        "kc_b": P(3.4, "-", "model", "Kasten & Czeplak (1980) cloud correction", "Cloud exponent"),
        "ground_albedo": P(0.2, "-", "handbook", DUFFIE, "Ground reflectance for reflected irradiance on vertical faces"),
        "cosz_min": P(0.02, "-", "assumption", "numerical guard", "Below this cos(zenith) beam irradiance is set to zero"),
    },
    # ------------------------------------------------------- heat transfer
    "heat": {
        "R_film_still": P(0.12, "m2K/W", "handbook", HANDBOOK_ASHRAE + " (still-air film, vertical surface)", "Still-air surface film resistance (convection + radiation) indoors/inside enclosures"),
        "hc_a": P(5.7, "W/m2K", "handbook", "McAdams wind correlation, as given in " + DUFFIE, "Outdoor convection h_c = a + b*v"),
        "hc_b": P(3.8, "W s/m3K", "handbook", "McAdams wind correlation, as given in " + DUFFIE, "Wind slope of outdoor convection"),
        "emissivity": P(0.9, "-", "handbook", HANDBOOK_INCROPERA + " (paper, paint, plastics ~0.9)", "Long-wave emissivity of package/mailbox surfaces"),
        "sigma": P(5.670e-8, "W/m2K4", "handbook", "Stefan-Boltzmann constant", "Used to linearise radiation h_r = 4*eps*sigma*T^3"),
        "lw_sky_deficit": P(63.0, "W/m2", "handbook", HANDBOOK_ASHRAE + " (sol-air temperature, horizontal surface)", "Long-wave sky radiation deficit for an upward face under clear sky; scaled by (1 - cloud)"),
        "porch_wind_factor": P(0.3, "-", "assumption", "sheltering of a doorstep vs the 10 m airport anemometer", "Wind at package = factor * station wind"),
        "porch_wind_min": P(0.5, "m/s", "assumption", "residual air movement", "Minimum wind at package"),
        "R_contact_floor": P(0.05, "m2K/W", "assumption", "contact of a soft package with a porch floor", "Resistance between package bottom and the floor surface"),
        "floor_absorptance": P(0.65, "-", "assumption", "weathered concrete/wood (typical 0.6-0.7)", "Solar absorptance of a sunlit porch floor"),
        "h_floor_eff": P(25.0, "W/m2K", "assumption", "effective loss coefficient incl. conduction into slab", "Floor sol-air rise = a_floor*GHI/h_floor_eff"),
        "shade_diffuse_factor": P(0.3, "-", "assumption", "covered porch sees part of the sky", "Fraction of diffuse irradiance reaching a package in shade"),
    },
    # --------------------------------------------------------- environments
    "env": {
        "pharmacy_c": P(22.0, "degC", "assumption", "pharmacy HVAC; inside USP controlled room temperature 20-25 C", "Pharmacy / dispensing area temperature"),
        "fridge_c": P(5.0, "degC", "regulatory", "label 2-8 C refrigerated storage (midpoint)", "Dispense temperature for refrigerated products"),
        "truck_beta": P(0.0, "degC per kW/m2", "free", "assumption; calibrated in VALIDATION.md (best fit to JAPhA 2023, 20-25 C reading; at the grid bound)", "Cargo-area rise above ambient per kW/m2 of horizontal sun", prior=10.0),
        "truck_tau_min": P(30.0, "min", "assumption", "thermal lag of a box truck cargo area", "First-order lag of cargo air towards its target"),
        "hub_f": P(0.0, "-", "free", "assumption; calibrated in VALIDATION.md (best fit to JAPhA 2023, 20-25 C reading; at the grid bound)", "Fraction of the outdoor swing that reaches a sorting hub (0 = fully conditioned at hub_set_c, 1 = unconditioned)", prior=1.0),
        "hub_set_c": P(22.0, "degC", "assumption", "conditioned-building reference", "Hub temperature if fully conditioned"),
        "hub_tau_h": P(4.0, "h", "assumption", "large unconditioned building lag", "Lag of hub air behind outdoor air"),
        "hub_gain_c": P(1.0, "degC", "assumption", "roof gain / equipment", "Offset of an unconditioned hub above lagged outdoor air"),
        "home_tau_h": P(6.0, "h", "assumption", "masonry apartment thermal lag (order of hours)", "Lag of indoor air behind outdoor air without AC"),
        "home_gain_c": P(1.5, "degC", "assumption", "internal + solar gains", "Indoor offset above lagged outdoor air without AC"),
        "home_topfloor_c": P(2.5, "degC", "assumption", "roof solar gain on top-floor units", "Extra offset for a top-floor apartment"),
        "home_ac_set_c": P(24.0, "degC", "assumption", "typical cooling setpoint", "Apartment with working AC: min(setpoint, no-AC temperature)"),
        "lobby_c": P(24.0, "degC", "assumption", "conditioned lobby / package room / pickup locker", "Indoor drop point temperature"),
    },
    # --------------------------------------------------------------- mailbox
    "mailbox": {
        "L": P(0.48, "m", "assumption", "standard curbside (T1-size) mailbox, approx.", "Length"),
        "W": P(0.165, "m", "assumption", "standard curbside (T1-size) mailbox, approx.", "Width"),
        "H": P(0.23, "m", "assumption", "standard curbside (T1-size) mailbox, approx.", "Height"),
        "mass_kg": P(1.8, "kg", "assumption", "thin galvanised/painted steel shell", "Shell mass"),
        "c": P(490.0, "J/kgK", "handbook", HANDBOOK_INCROPERA + " (carbon steel)", "Specific heat of steel"),
        "absorptance": P(0.9, "-", "assumption", "dark painted metal (black paint 0.9-0.97)", "Solar absorptance of shell"),
    },
    # ------------------------------------------------------------- numerics
    "num": {
        "dt_s": P(60.0, "s", "assumption", "numerical", "Integration step (exponential integrator, unconditionally stable)"),
    },
    # -------------------------------------------------------------- kinetics
    "mkt": {
        "delta_h_kj_mol": P(83.144, "kJ/mol", "regulatory", "USP <1079.2> default activation energy for MKT", "Default activation energy (configurable per drug)"),
        "R_gas": P(8.3144, "J/molK", "handbook", "gas constant", "Universal gas constant"),
    },
}


@dataclass
class Packaging:
    id: str
    label: str
    L: float  # outer dims, m
    W: float
    H: float
    R_wall: float  # m2K/W
    absorptance: float
    contents_kg: float
    contents_c: float  # J/kgK
    coolant_kg: float = 0.0
    coolant_start_c: float = 0.0
    coolant_type: str = "water_gel"
    coolant_G_W_K: float = 1.0  # product-to-coolant conductance (W/K)
    wall_c_per_area: float = 0.0  # J/m2K heat capacity of the insulating layer (0 = pure resistance)
    sources: Dict[str, str] = field(default_factory=dict)


COOLANT_TYPES: Dict[str, Dict[str, P]] = {
    "water_gel": {
        "melt_c": P(0.0, "degC", "handbook", "water-based gel packs melt near 0 C", "Melting point of gel/ice packs"),
        "latent_j_kg": P(334000.0, "J/kg", "handbook", HANDBOOK_INCROPERA + " (latent heat of fusion of water)", "Latent heat of fusion"),
        "c_solid": P(2050.0, "J/kgK", "handbook", HANDBOOK_INCROPERA + " (ice)", "Specific heat, frozen"),
        "c_liquid": P(4186.0, "J/kgK", "handbook", HANDBOOK_INCROPERA + " (water)", "Specific heat, liquid (gel packs ~ water)"),
    },
    "pcm_22": {
        "melt_c": P(22.0, "degC", "assumption", "room-temperature phase-change packs sold for controlled-room-temperature shipping (melt ~20-22 C)", "Melting point of a CRT phase-change pack"),
        "latent_j_kg": P(180000.0, "J/kg", "assumption", "paraffin / salt-hydrate PCMs are typically 150-250 kJ/kg", "Latent heat of the PCM"),
        "c_solid": P(2000.0, "J/kgK", "assumption", "paraffin-type PCM", "Specific heat, solid"),
        "c_liquid": P(2200.0, "J/kgK", "assumption", "paraffin-type PCM", "Specific heat, liquid"),
    },
}

COOLANT = {
    "wall_fraction": P(0.8, "-", "assumption", "standard pack-out: packs placed around the payload (top, bottom, sides)", "Share of wall heat flow intercepted by the coolant before it reaches the product"),
}

_SMALL = dict(L=0.25, W=0.18, H=0.05)
_BOX = dict(L=0.30, W=0.25, H=0.25)
# 38 mm (1.5 in) EPS: thickness * density * specific heat = 0.038 m * 20 kg/m3 * 1300 J/kgK
# (EPS density 15-30 kg/m3 and c ~1300 J/kgK: handbook ranges)
_EPS_C = 0.038 * 20.0 * 1300.0
_C_CONTENTS = 1500.0

PACKAGING: Dict[str, Packaging] = {
    "poly_mailer": Packaging(
        "poly_mailer", "Plain poly mailer", **_SMALL, R_wall=0.002, absorptance=0.4,
        contents_kg=0.25, contents_c=_C_CONTENTS,
        sources={
            "R_wall": "assumption: 0.07 mm LDPE + thin paper bag, k~0.3 W/mK -> negligible",
            "absorptance": "assumption: white/grey film 0.3-0.5",
            "dims": "assumption: typical pharmacy mailer 25x18x5 cm",
            "contents": "assumption: 0.25 kg of bottles/pens/paper, c ~1500 J/kgK (plastic 1500-1900, glass 840, paper 1340)",
        }),
    "padded_mailer": Packaging(
        "padded_mailer", "Padded (bubble) mailer", **_SMALL, R_wall=0.1, absorptance=0.75,
        contents_kg=0.25, contents_c=_C_CONTENTS,
        sources={
            "R_wall": "assumption: ~4 mm bubble lining, k~0.04 W/mK -> 0.1 m2K/W",
            "absorptance": "assumption: kraft paper 0.7-0.8",
        }),
    "insulated_box": Packaging(
        "insulated_box", "Insulated box (38 mm EPS + carton)", **_BOX, R_wall=1.15, absorptance=0.75,
        contents_kg=0.25, contents_c=_C_CONTENTS, wall_c_per_area=_EPS_C,
        sources={
            "wall_c": "38 mm EPS, density 20 kg/m3 (handbook range 15-30), c 1300 J/kgK -> 988 J/m2K, modeled as a mid-wall node (2R1C)",
            "R_wall": "38 mm (1.5 in) EPS, k=0.035 W/mK (handbook range 0.033-0.040) -> 1.09, + corrugated carton ~0.06",
            "absorptance": "assumption: brown corrugated carton 0.7-0.8",
            "dims": "assumption: small pharmacy cold-chain shipper 30x25x25 cm",
        }),
    "insulated_box_cold_pack": Packaging(
        "insulated_box_cold_pack", "Insulated box + 3 refrigerated gel packs (5 C)", **_BOX, R_wall=1.15, absorptance=0.75,
        contents_kg=0.25, contents_c=_C_CONTENTS, coolant_kg=1.5, coolant_start_c=5.0, wall_c_per_area=_EPS_C,
        sources={"coolant": "assumption: 3 x 0.5 kg gel packs conditioned in a 2-8 C fridge (no latent heat available); product-coolant conductance 1.0 W/K (assumption)"}),
    "insulated_box_frozen_pack": Packaging(
        "insulated_box_frozen_pack", "Insulated box + 3 frozen gel packs (-10 C)", **_BOX, R_wall=1.15, absorptance=0.75,
        contents_kg=0.25, contents_c=_C_CONTENTS, coolant_kg=1.5, coolant_start_c=-10.0, wall_c_per_area=_EPS_C,
        sources={"coolant": "assumption: 3 x 0.5 kg gel packs from a freezer at -10 C (uses latent heat of melting); payload in contact with packs through a thin divider (product-coolant conductance 1.0 W/K, assumption)"}),
    "insulated_box_frozen_pack_buffered": Packaging(
        "insulated_box_frozen_pack_buffered", "Insulated box + 3 conditioned frozen gel packs (~0 C) with a buffer around the product", **_BOX,
        R_wall=1.15, absorptance=0.75, contents_kg=0.25, contents_c=_C_CONTENTS, coolant_kg=1.5, coolant_start_c=-0.5,
        coolant_G_W_K=0.15, wall_c_per_area=_EPS_C,
        sources={"coolant": "assumption: frozen packs 'conditioned' at room temperature until they start to melt (-0.5 C, still solid: full latent heat available) and a bubble-wrap/cardboard buffer around the payload (product-coolant conductance 0.15 W/K), the usual way to avoid freezing insulin"}),
    "insulated_box_crt_pcm": Packaging(
        "insulated_box_crt_pcm", "Insulated box + 3 room-temperature phase-change packs (22 C)", **_BOX, R_wall=1.15, absorptance=0.75,
        contents_kg=0.25, contents_c=_C_CONTENTS, coolant_kg=1.5, coolant_start_c=18.0, coolant_type="pcm_22",
        wall_c_per_area=_EPS_C,
        sources={"coolant": "assumption: 3 x 0.5 kg 22 C phase-change packs conditioned solid at 18 C, so a room-temperature drug is neither heated above ~22 C nor chilled below 15 C while they melt"}),
}

# Environment codes shared with TypeScript (keep in sync: generated).
ENVIRONMENTS: List[str] = [
    "pharmacy", "fridge", "truck", "hub", "porch_shade", "porch_sun", "mailbox_sun",
    "lobby", "home_ac", "home_noac", "home_noac_top",
]
ENV_LABELS = {
    "pharmacy": "Climate-controlled pharmacy",
    "fridge": "Pharmacy refrigerator",
    "truck": "Delivery truck / trailer cargo area",
    "hub": "Carrier sorting hub",
    "porch_shade": "Doorstep in shade",
    "porch_sun": "Doorstep in direct sun",
    "mailbox_sun": "Metal mailbox in sun",
    "lobby": "Building lobby / package room / pickup locker",
    "home_ac": "Apartment with AC",
    "home_noac": "Apartment without AC",
    "home_noac_top": "Top-floor apartment without AC",
}


def v(section: str, key: str) -> float:
    return PARAMS[section][key].value


def flat_values() -> Dict[str, Dict[str, float]]:
    out = {s: {k: p.value for k, p in d.items()} for s, d in PARAMS.items()}
    out["coolant"] = {k: p.value for k, p in COOLANT.items()}
    out["coolant_types"] = {t: {k: p.value for k, p in d.items()} for t, d in COOLANT_TYPES.items()}
    return out


def set_free(**kw: float) -> None:
    """Override free parameters (used by calibration)."""
    for k, val in kw.items():
        sec = "env"
        assert PARAMS[sec][k].kind == "free", k
        PARAMS[sec][k].value = float(val)
