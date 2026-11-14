"""Physics and honesty-rule tests.

Run:  cd scripts && uv run --python 3.12 --with numpy,pandas,pytest python -m pytest thermal_sim/tests -q
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from thermal_sim import params
from thermal_sim.advice import assess, load_profiles
from thermal_sim.metrics import mkt_c, summarize
from thermal_sim.model import Weather, simulate_legs, solar

REPO = Path(__file__).resolve().parents[3]
H = 3600.0


def const_weather(temp=25.0, cloud=1.0, wind=2.0, start="2025-06-20T00:00:00", hours=96) -> Weather:
    t0 = datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp()
    return Weather(t0, np.full(hours, temp), np.full(hours, wind), np.full(hours, cloud))


def night(w: Weather, day_offset=1) -> float:
    # 06:00 UTC = 02:00 EDT: sun well below the horizon in NYC in June
    return w.start + (24 * day_offset + 6) * H


# ------------------------------------------------------------ energy balance
@pytest.mark.parametrize("env", ["pharmacy", "porch_shade", "porch_sun", "truck", "mailbox_sun"])
@pytest.mark.parametrize("pkg", ["poly_mailer", "padded_mailer", "insulated_box"])
def test_no_sun_equal_temps_no_change(env, pkg):
    temp = 22.0 if env == "pharmacy" else 25.0
    w = const_weather(temp=temp, cloud=1.0)
    t = night(w)
    r = simulate_legs(w, [(env, t, t + 2 * H)], pkg, temp)
    assert np.max(np.abs(r["temp"] - temp)) < 1e-9


def test_steady_state_approaches_env():
    w = const_weather(temp=30.0)
    t = night(w)
    r = simulate_legs(w, [("truck", t, t + 3 * H)], "poly_mailer", 20.0)  # truck = ambient at night
    assert abs(r["temp"][-1] - 30.0) < 0.01
    assert np.all(np.diff(r["temp"]) >= -1e-12)  # monotone warming, no overshoot
    assert r["temp"].max() <= 30.0 + 1e-9


def test_steady_state_insulated_box_too():
    w = const_weather(temp=30.0)
    t = night(w)
    r = simulate_legs(w, [("pharmacy", t, t + 12 * H)], "insulated_box", 30.0)
    assert abs(r["temp"][-1] - params.v("env", "pharmacy_c")) < 0.05
    assert r["temp"].min() >= params.v("env", "pharmacy_c") - 1e-9  # no undershoot


def test_sun_heats_above_air():
    w = const_weather(temp=30.0, cloud=0.0)
    noon = w.start + (24 + 17) * H  # 13:00 EDT
    sun = simulate_legs(w, [("porch_sun", noon, noon + 2 * H)], "poly_mailer", 30.0)
    shade = simulate_legs(w, [("porch_shade", noon, noon + 2 * H)], "poly_mailer", 30.0)
    assert sun["temp"][-1] > shade["temp"][-1] > 30.0


# ------------------------------------------------------------------ MKT
def test_mkt_constant():
    assert mkt_c([25.0] * 50) == pytest.approx(25.0, abs=1e-9)
    assert mkt_c([40.0] * 3, delta_h_kj_mol=60.0) == pytest.approx(40.0, abs=1e-9)


def test_mkt_ge_mean_for_fluctuating():
    rng = np.random.default_rng(0)
    for _ in range(50):
        x = rng.uniform(5, 60, 200)
        assert mkt_c(x) >= x.mean() - 1e-12
    x = [20.0, 30.0]
    assert mkt_c(x) > 25.0


def test_mkt_reference_value():
    # dH/R = 10000 K with the USP default; two equal halves at 20 and 30 C
    a = 83144.0 / 8.3144
    tk = np.array([293.15, 303.15])
    expected = a / -np.log(np.mean(np.exp(-a / tk))) - 273.15
    assert mkt_c([20.0, 30.0]) == pytest.approx(expected, abs=1e-9)


# ------------------------------------------------------------ packaging
def test_insulated_box_lags_plain_mailer():
    w = const_weather(temp=35.0)
    t = night(w)
    legs = [("truck", t, t + 4 * H)]
    poly = simulate_legs(w, legs, "poly_mailer", 22.0)["temp"]
    box = simulate_legs(w, legs, "insulated_box", 22.0)["temp"]
    assert box[30] < poly[30] - 2.0  # after 30 min
    t_poly = np.argmax(poly > 30.0)
    t_box = np.argmax(box > 30.0)
    assert t_box > 2 * t_poly


def test_frozen_pack_plateau_and_delay():
    w = const_weather(temp=35.0)
    t = night(w)
    legs = [("truck", t, t + 10 * H)]
    r = simulate_legs(w, legs, "insulated_box_frozen_pack", 22.0)
    cool = r["coolant"]
    assert np.sum(np.isclose(cool, 0.0)) > 60  # >1 h melting at 0 C
    box = simulate_legs(w, legs, "insulated_box", 22.0)["temp"]
    assert r["temp"][240] < box[240] - 5.0


def test_pcm_pack_holds_crt_band():
    w = const_weather(temp=35.0)
    t = night(w)
    r = simulate_legs(w, [("truck", t, t + 6 * H)], "insulated_box_crt_pcm", 22.0)["temp"]
    assert r.min() >= 15.0 and r[: 4 * 60].max() <= 25.0


# ------------------------------------------------------------------ solar
def test_solar_noon_and_night():
    t_noon = datetime(2025, 6, 21, 17, 0, tzinfo=timezone.utc).timestamp()  # ~solar noon NYC
    s = solar(np.array([t_noon]), np.array([0.0]))
    assert 0.94 < s["cosz"][0] < 0.97
    assert 850 < s["ghi"][0] < 1050
    t_night = datetime(2025, 6, 21, 6, 0, tzinfo=timezone.utc).timestamp()
    s = solar(np.array([t_night]), np.array([0.0]))
    assert s["ghi"][0] == 0 and s["dni"][0] == 0
    cloudy = solar(np.array([t_noon]), np.array([1.0]))
    assert cloudy["ghi"][0] == pytest.approx(0.25 * 1098 * 0.955 * np.exp(-0.057 / 0.955), rel=0.05)


# ------------------------------------------------------------------ advice
PROFILES = load_profiles()


def trace(level, minutes, base=22.0):
    return np.array([base] + [level] * minutes + [base] * 10)


def test_advice_tiers():
    epi = PROFILES["epinephrine_autoinjector"]
    assert assess(trace(24.0, 60), epi)["tier"] == "use_as_normal"
    a = assess(trace(45.0, 60), epi)
    assert a["tier"] == "check_with_pharmacist" and a["matched_evidence"] == "rachid2016_70c_5d"
    assert assess(trace(75.0, 60), epi)["tier"] == "request_replacement"
    ins = PROFILES["insulin_pen"]
    assert assess(trace(36.0, 120, base=5.0), ins)["tier"] == "check_with_pharmacist"
    assert assess(trace(39.0, 120, base=5.0), ins)["tier"] == "request_replacement"
    assert assess(trace(-1.0, 30, base=5.0), ins)["tier"] == "request_replacement"  # frozen
    strips = PROFILES["glucose_test_strips"]
    a = assess(trace(43.0, 20), strips)
    assert a["tier"] == "request_replacement" and a["matched_evidence"] == "louie2014_42c"
    tab = PROFILES["oral_tablet_crt"]
    assert assess(trace(38.0, 120), tab)["tier"] == "use_as_normal"  # USP spike allowance
    assert assess(trace(45.0, 30), tab)["tier"] == "request_replacement"
    glp = PROFILES["glp1_pen"]
    assert assess(trace(31.0, 30, base=5.0), glp)["tier"] == "request_replacement"  # no studies


def test_honesty_rule_no_potency_numbers():
    """Advice never contains a percentage (no '% potency left')."""
    rng = np.random.default_rng(1)
    for p in PROFILES.values():
        for txt in p["advice_text"].values():
            assert "%" not in txt
        for _ in range(20):
            x = np.concatenate([[22.0], rng.uniform(-5, 90, 300)])
            a = assess(x, p)
            assert a["tier"] in ("use_as_normal", "check_with_pharmacist", "request_replacement")
            blob = json.dumps({k: a[k] for k in ("message", "reasons", "action")})
            assert "%" not in blob and "potency" not in blob.lower()


def test_profiles_cite_only_marked_sources():
    data = json.loads((REPO / "data/processed/drug_storage_profiles.json").read_text())
    allowed = set(data["citation_status_key"])
    for p in data["profiles"]:
        assert p["label"]["citation_status"] in allowed
        for ev in p["evidence"]:
            assert ev["citation"]["status"] in allowed, ev["id"]
            if ev["used_in_rule"]:
                assert ev["exposure"]["temp_c"] is not None and ev["exposure"]["hours"] is not None


# ------------------------------------------------------------ consistency
def test_generated_artifacts_match_params():
    flat = params.flat_values()
    scen = REPO / "data/processed/thermal_scenarios.json"
    if scen.exists():
        assert json.loads(scen.read_text())["params"] == json.loads(json.dumps(flat))
    ts = (REPO / "lib/thermal/params.ts").read_text()
    assert f'"truck_beta": {flat["env"]["truck_beta"]}' in ts
    val = Path(__file__).resolve().parents[1] / "validation_results.json"
    if val.exists():
        adopted = json.loads(val.read_text())["adopted"]
        assert adopted["truck_beta"] == flat["env"]["truck_beta"]
        assert adopted["hub_f"] == flat["env"]["hub_f"]
