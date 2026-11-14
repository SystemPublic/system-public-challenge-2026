"""Lumped-capacitance thermal model of a medicine package.

Physics (per time step ``dt``)
------------------------------
The product (drug + its immediate containers + paper, one lumped node of heat
capacity ``C = m*c``) exchanges heat with its surroundings through the package
faces.  Each face f (top, sides, bottom) has

* an *outside driving temperature*, the **sol-air temperature**
  ``T_sa,f = T_air + alpha*q_f/h_o - eps*dR*(1-cloud)/h_o``  (ASHRAE), where
  ``q_f`` is the solar irradiance on that face and the last term is the
  long-wave sky deficit (top face only, outdoors in the open);
* a series thermal resistance ``1/U_f = 1/h_o + R_wall + R_film_inside``
  (outside film, packaging layer, still-air film around the product).

so that  ``C dT/dt = sum_f U_f A_f (T_sa,f - T)``.

With no packaging resistance and no inside film this reduces exactly to the
textbook form ``m c dT/dt = h A (T_env - T) + alpha A_sun G``: the sol-air
formulation just splits absorbed sun correctly between "lost back outside" and
"conducted inward" once there is insulation in the way.

Optional gel/ice packs form a second node described by its enthalpy (sensible
heat + latent heat of melting at 0 C).  The wall heat flow is shared between
product and coolant; product and coolant also exchange heat directly.

Each node is advanced with an exponential integrator (exact for a fixed
boundary over the step), so the scheme is stable for any ``dt``.

Environments with their own memory (truck cargo air, metal mailbox shell) are
state variables advanced alongside the product; building interiors (hub,
apartment) are first-order lags of the hourly outdoor temperature.

Everything here is vectorised over a leading sample axis N so the same code
runs one scenario (N=1) or a Monte-Carlo batch.  ``lib/thermal/model.ts`` is a
line-by-line scalar port; keep them in sync.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .params import COOLANT, COOLANT_TYPES, ENVIRONMENTS, PACKAGING, Packaging, v

ENV_CODE: Dict[str, int] = {name: i for i, name in enumerate(ENVIRONMENTS)}
TWO_OVER_PI = 2.0 / math.pi


# ---------------------------------------------------------------- weather
@dataclass
class Weather:
    """Regular hourly weather series (UTC epoch seconds of the first hour)."""

    start: float
    temp_c: np.ndarray
    wind_ms: np.ndarray
    cloud: np.ndarray  # fraction 0..1
    step: float = 3600.0

    def __post_init__(self) -> None:
        self.temp_c = np.asarray(self.temp_c, float)
        self.wind_ms = np.asarray(self.wind_ms, float)
        self.cloud = np.clip(np.asarray(self.cloud, float), 0.0, 1.0)
        self.hours = self.start + self.step * np.arange(len(self.temp_c))
        self.hub_ema = ema_hourly(self.temp_c, v("env", "hub_tau_h"))
        self.home_ema = ema_hourly(self.temp_c, v("env", "home_tau_h"))

    def at(self, arr: np.ndarray, t: np.ndarray) -> np.ndarray:
        # linear interpolation, clamped at both ends
        return np.interp(t, self.hours, arr)

    def to_json(self) -> dict:
        return {
            "start_utc": self.start,
            "step_s": self.step,
            "temp_c": [round(float(x), 2) for x in self.temp_c],
            "wind_ms": [round(float(x), 2) for x in self.wind_ms],
            "cloud": [round(float(x), 3) for x in self.cloud],
        }

    @classmethod
    def from_json(cls, d: dict) -> "Weather":
        return cls(d["start_utc"], d["temp_c"], d["wind_ms"], d["cloud"], d.get("step_s", 3600.0))


def ema_hourly(temp: np.ndarray, tau_h: float) -> np.ndarray:
    """First-order lag on an hourly grid, initialised at the first value."""
    a = 1.0 - math.exp(-1.0 / tau_h)
    out = np.empty(len(temp))
    acc = float(temp[0])
    for i, x in enumerate(temp):
        if i > 0:
            acc = acc + a * (float(x) - acc)
        out[i] = acc
    return out


# ------------------------------------------------------------------ solar
def day_of_year_and_hour(t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """UTC day-of-year (1..366) and fractional UTC hour for epoch seconds."""
    t = np.asarray(t, float)
    days = np.floor(t / 86400.0)
    hour = (t - days * 86400.0) / 3600.0
    # day of year via calendar: vectorise with a small cache
    uniq = np.unique(days)
    doy_map = {d: datetime.fromtimestamp(d * 86400.0, tz=timezone.utc).timetuple().tm_yday for d in uniq}
    doy = np.vectorize(doy_map.__getitem__, otypes=[float])(days) if days.size else days
    return doy, hour


def solar(t: np.ndarray, cloud: np.ndarray) -> Dict[str, np.ndarray]:
    """Sun position (NOAA 'General Solar Position Calculations', Spencer 1971
    series) + Haurwitz clear-sky GHI + Kasten-Czeplak cloud correction + Erbs
    diffuse split.  Returns cosZ, sinZ, GHI, DNI, DHI (W/m2)."""
    lat = math.radians(v("site", "lat_deg"))
    lon = v("site", "lon_deg")
    doy, hour = day_of_year_and_hour(t)
    g = 2.0 * math.pi / 365.0 * (doy - 1.0 + (hour - 12.0) / 24.0)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
                    - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    tst = hour * 60.0 + eqt + 4.0 * lon
    ha = np.radians(tst / 4.0 - 180.0)
    cosz = math.sin(lat) * np.sin(decl) + math.cos(lat) * np.cos(decl) * np.cos(ha)
    cosz = np.clip(cosz, -1.0, 1.0)
    sinz = np.sqrt(1.0 - cosz * cosz)
    up = cosz > v("solar", "cosz_min")
    cz = np.where(up, cosz, 1.0)
    ghi_clear = np.where(up, v("solar", "haurwitz_a") * cz * np.exp(-v("solar", "haurwitz_b") / cz), 0.0)
    ghi = ghi_clear * (1.0 - v("solar", "kc_a") * np.power(np.clip(cloud, 0, 1), v("solar", "kc_b")))
    i0 = v("solar", "solar_const") * (1.0 + 0.033 * np.cos(2.0 * math.pi * doy / 365.0))
    kt = np.where(up, ghi / (i0 * cz), 0.0)
    df = np.where(kt <= 0.22, 1.0 - 0.09 * kt,
                  np.where(kt <= 0.8,
                           0.9511 - 0.1604 * kt + 4.388 * kt ** 2 - 16.638 * kt ** 3 + 12.336 * kt ** 4,
                           0.165))
    dhi = ghi * df
    dni = np.where(up, (ghi - dhi) / cz, 0.0)
    cosz_eff = np.where(up, cosz, 0.0)
    return {"cosz": cosz_eff, "sinz": np.where(up, sinz, 0.0), "ghi": ghi, "dni": dni, "dhi": dhi}


# ----------------------------------------------------------- package geometry
def pkg_geometry(p: Packaging) -> Dict[str, float]:
    a_top = p.L * p.W
    a_side = 2.0 * (p.L + p.W) * p.H
    return {
        "a_top": a_top,
        "a_bot": a_top,
        "a_side": a_side,
        "side_beam_proj": TWO_OVER_PI * p.H * (p.L + p.W),  # mean sunlit projection, random azimuth
    }


def coolant_props(p: Packaging) -> Tuple[float, float, float, float]:
    d = COOLANT_TYPES[p.coolant_type]
    return d["melt_c"].value, d["latent_j_kg"].value, d["c_solid"].value, d["c_liquid"].value


def coolant_T(H, m, melt, L, cs, cl):
    """Coolant temperature from enthalpy H (J, zero = solid at its melting point)."""
    msafe = np.where(m > 0, m, 1.0)
    return np.where(H < 0, melt + H / (msafe * cs),
                    np.where(H <= msafe * L, melt, melt + (H - msafe * L) / (msafe * cl)))


def coolant_H(Tc, m, melt, L, cs, cl):
    return np.where(Tc < melt, m * cs * (Tc - melt), m * L + m * cl * (Tc - melt))


# ------------------------------------------------------------------ engine
def run(weather: Weather, times: np.ndarray, env: np.ndarray, pkg_ids: Sequence[str],
        T0: np.ndarray) -> Dict[str, np.ndarray]:
    """Integrate N samples over K steps.

    times : (N, K) epoch seconds at the start of each step (uniform dt)
    env   : (N, K) int environment codes (see ENVIRONMENTS)
    returns dict with 'temp' (N, K+1) product temperature, 'coolant' (N, K+1).
    """
    times = np.atleast_2d(np.asarray(times, float))
    env = np.atleast_2d(np.asarray(env, int))
    N, K = times.shape
    dt = v("num", "dt_s")
    pk = [PACKAGING[i] for i in pkg_ids]
    geo = [pkg_geometry(p) for p in pk]
    A_top = np.array([g["a_top"] for g in geo])
    A_bot = np.array([g["a_bot"] for g in geo])
    A_side = np.array([g["a_side"] for g in geo])
    side_proj = np.array([g["side_beam_proj"] for g in geo])
    R_wall = np.array([p.R_wall for p in pk])
    alpha = np.array([p.absorptance for p in pk])
    C = np.array([p.contents_kg * p.contents_c for p in pk])
    mc = np.array([p.coolant_kg for p in pk])
    has_c = mc > 0
    Cw = np.array([p.wall_c_per_area for p in pk]) * (A_top + A_bot + A_side)
    has_w = Cw > 0
    T = np.asarray(T0, float).reshape(N).copy()
    Tw = T.copy()  # wall node starts at product temperature
    cp = np.array([coolant_props(p) for p in pk]).reshape(N, 4)
    c_melt, c_L, c_cs, c_cl = cp[:, 0], cp[:, 1], cp[:, 2], cp[:, 3]
    H = coolant_H(np.array([p.coolant_start_c for p in pk]), mc, c_melt, c_L, c_cs, c_cl)

    R_in = v("heat", "R_film_still")
    h_still = 1.0 / R_in
    eps = v("heat", "emissivity")
    sigma = v("heat", "sigma")
    dR = v("heat", "lw_sky_deficit")
    rho_g = v("solar", "ground_albedo")
    f_sh = v("heat", "shade_diffuse_factor")
    fwall = COOLANT["wall_fraction"].value
    Gpc = np.array([p.coolant_G_W_K for p in pk])
    # mailbox
    mbL, mbW, mbH = v("mailbox", "L"), v("mailbox", "W"), v("mailbox", "H")
    mb_top = mbL * mbW
    mb_side = 2.0 * (mbL + mbW) * mbH
    mb_proj = TWO_OVER_PI * mbH * (mbL + mbW)
    mb_area = 2.0 * mb_top + mb_side
    mb_C = v("mailbox", "mass_kg") * v("mailbox", "c")
    mb_alpha = v("mailbox", "absorptance")
    beta = v("env", "truck_beta")
    tau_truck = v("env", "truck_tau_min") * 60.0
    hub_f = v("env", "hub_f")
    hub_set = v("env", "hub_set_c")
    hub_gain = v("env", "hub_gain_c")

    temps = np.empty((N, K + 1))
    cool = np.empty((N, K + 1))
    temps[:, 0] = T
    cool[:, 0] = np.where(has_c, coolant_T(H, mc, c_melt, c_L, c_cs, c_cl), np.nan)
    truck = None
    mbox = None

    for k in range(K):
        t = times[:, k]
        e = env[:, k]
        Ta = weather.at(weather.temp_c, t)
        wind = weather.at(weather.wind_ms, t)
        cl = weather.at(weather.cloud, t)
        s = solar(t, cl)
        ghi, dni, dhi, cz, sz = s["ghi"], s["dni"], s["dhi"], s["cosz"], s["sinz"]

        # outdoor film coefficient (porch-level wind)
        vp = np.maximum(v("heat", "porch_wind_factor") * wind, v("heat", "porch_wind_min"))
        Tk = Ta + 273.15
        h_o = v("heat", "hc_a") + v("heat", "hc_b") * vp + 4.0 * eps * sigma * Tk ** 3
        lw = eps * dR * (1.0 - cl) / h_o

        # --- environment states (initialised at quasi-steady values) ---
        truck_target = Ta + beta * ghi / 1000.0
        if truck is None:
            truck = truck_target.copy()
        mb_abs = mb_alpha * (mb_top * (dni * cz + dhi) + mb_proj * dni * sz
                             + mb_side * 0.5 * (dhi + rho_g * ghi))
        mb_G = h_o * mb_area
        mb_target = Ta + (mb_abs - eps * dR * (1.0 - cl) * mb_top) / mb_G
        if mbox is None:
            mbox = mb_target.copy()

        hub_T = hub_set + hub_f * (weather.at(weather.hub_ema, t) + hub_gain - hub_set)
        noac = weather.at(weather.home_ema, t) + v("env", "home_gain_c")

        # --- face boundary conditions for each environment ---
        indoor_T = np.select(
            [e == ENV_CODE["pharmacy"], e == ENV_CODE["fridge"], e == ENV_CODE["truck"], e == ENV_CODE["hub"],
             e == ENV_CODE["mailbox_sun"], e == ENV_CODE["lobby"], e == ENV_CODE["home_ac"],
             e == ENV_CODE["home_noac"], e == ENV_CODE["home_noac_top"]],
            [np.full(N, v("env", "pharmacy_c")), np.full(N, v("env", "fridge_c")), truck, hub_T,
             mbox, np.full(N, v("env", "lobby_c")), np.minimum(v("env", "home_ac_set_c"), noac),
             noac, noac + v("env", "home_topfloor_c")],
            default=Ta,
        )
        sun = e == ENV_CODE["porch_sun"]
        shade = e == ENV_CODE["porch_shade"]
        outdoor = sun | shade

        # irradiance on faces (W/m2) -- only used outdoors
        q_top = np.where(sun, dni * cz + dhi, f_sh * dhi)
        q_side = np.where(sun, (side_proj * dni * sz + A_side * 0.5 * (dhi + rho_g * ghi)) / A_side,
                          f_sh * 0.5 * (dhi + rho_g * ghi))
        T_floor = np.where(sun, Ta + v("heat", "floor_absorptance") * ghi / v("heat", "h_floor_eff"), Ta)

        Tsa_top = np.where(outdoor, Ta + alpha * q_top / h_o - np.where(sun, lw, 0.0), indoor_T)
        Tsa_side = np.where(outdoor, Ta + alpha * q_side / h_o, indoor_T)
        Tsa_bot = np.where(outdoor, T_floor, indoor_T)
        hf = np.where(outdoor, h_o, h_still)
        R_out_b = np.where(outdoor, v("heat", "R_contact_floor"), 1.0 / hf)
        # without a wall node: outside film + whole wall + inside film in series
        # with a wall node (2R1C): outside film + half wall -> node -> half wall + inside film
        R_ow = np.where(has_w, 0.5 * R_wall, R_wall + R_in)
        U_ts = 1.0 / (1.0 / hf + R_ow)
        U_b = 1.0 / (R_out_b + R_ow)
        G_o = U_ts * (A_top + A_side) + U_b * A_bot
        T_o = (U_ts * (A_top * Tsa_top + A_side * Tsa_side) + U_b * A_bot * Tsa_bot) / G_o
        G_i = (A_top + A_side + A_bot) / (0.5 * R_wall + R_in)
        G_w = np.where(has_w, G_i, G_o)          # conductance seen by the interior
        T_eq = np.where(has_w, Tw, T_o)          # driving temperature seen by the interior

        # --- product (+ coolant) update ---
        Tc = coolant_T(H, mc, c_melt, c_L, c_cs, c_cl)
        G_p = np.where(has_c, (1.0 - fwall) * G_w + Gpc, G_w)
        T_eqp = np.where(has_c, ((1.0 - fwall) * G_w * T_eq + Gpc * Tc) / G_p, T_eq)
        T_new = T_eqp + (T - T_eqp) * np.exp(-dt * G_p / C)
        Qc = np.where(has_c, fwall * G_w * (T_eq - Tc) + Gpc * (T - Tc), 0.0)
        H = H + Qc * dt
        # wall node (uses start-of-step product temperature)
        Gwt = G_o + G_i
        Tw_tgt = (G_o * T_o + G_i * T) / Gwt
        Cw_safe = np.where(has_w, Cw, 1.0)
        Tw = np.where(has_w, Tw_tgt + (Tw - Tw_tgt) * np.exp(-dt * Gwt / Cw_safe), T_new)
        T = T_new

        # --- advance environment states ---
        truck = truck_target + (truck - truck_target) * math.exp(-dt / tau_truck)
        mbox = mb_target + (mbox - mb_target) * np.exp(-dt * mb_G / mb_C)

        temps[:, k + 1] = T
        cool[:, k + 1] = np.where(has_c, coolant_T(H, mc, c_melt, c_L, c_cs, c_cl), np.nan)
    return {"temp": temps, "coolant": cool}


# ------------------------------------------------------------- itineraries
Leg = Tuple[str, float, float]  # (environment, start epoch, end epoch)


def legs_to_grid(legs: List[Leg]) -> Tuple[np.ndarray, np.ndarray]:
    """Turn a leg list into per-step (times, env codes) for one sample."""
    dt = v("num", "dt_s")
    t0, t1 = legs[0][1], legs[-1][2]
    K = int(round((t1 - t0) / dt))
    times = t0 + dt * np.arange(K)
    env = np.empty(K, int)
    for name, a, b in legs:
        env[(times >= a - 1e-6) & (times < b - 1e-6)] = ENV_CODE[name]
    return times, env


def simulate_legs(weather: Weather, legs: List[Leg], pkg_id: str, T0: float) -> Dict[str, np.ndarray]:
    times, env = legs_to_grid(legs)
    out = run(weather, times[None, :], env[None, :], [pkg_id], np.array([T0]))
    t_all = np.append(times, times[-1] + v("num", "dt_s"))
    return {"t": t_all, "temp": out["temp"][0], "coolant": out["coolant"][0], "env": env}
