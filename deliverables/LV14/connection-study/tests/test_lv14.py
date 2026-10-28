import json
import math
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "model"))
R = HERE / "results"

import cable as C  # noqa: E402
import faults as F  # noqa: E402
import grading as G  # noqa: E402


def test_cable_rating_matches_independent_arithmetic():
    x = replace(C.Inputs(un_kv=220.0, t_ins_mm=24.0), area_mm2=500)
    i, p = C.rating_a(x)
    dc = math.sqrt(4 * 500 / (math.pi * 0.92)) / 1000
    t1 = 3.5 / (2 * math.pi) * math.log(1 + 2 * 0.024 / dc)
    assert abs(t1 - p["T1"]) < 1e-12
    u = 2 * 1.0 / (p["d_ext_mm"] / 1000)
    t4 = 1.0 / (2 * math.pi) * math.log(u + math.sqrt(u * u - 1))
    assert abs(t4 - p["T4"]) < 1e-12
    r = p["R_uohm_m"] * 1e-6
    num = 75 - 0.5 * p["Wd"] * t1 - 3 * p["Wd"] * (p["T3"] + t4)
    den = r * t1 + 3 * r * 1.1 * (p["T3"] + t4)
    assert abs(math.sqrt(num / den) / i - 1) < 0.005


def test_chosen_size_is_smallest_that_meets_design_current():
    s = json.load(open(R / "cable_sizing.json"))
    for k in ("array", "export"):
        o = s[k]
        rows = {r["area"]: r["rating_a"] for r in o["table"]}
        assert rows[o["chosen_mm2"]] >= o["design_a"]
        smaller = [a for a in rows if a < o["chosen_mm2"]]
        assert rows[max(smaller)] < o["design_a"]


def test_rating_rises_with_area_and_falls_with_soil_resistivity():
    x = C.Inputs(un_kv=66.0, t_ins_mm=10.0)
    r = [C.rating_a(replace(x, area_mm2=a))[0] for a in C.SERIES]
    assert all(b > a for a, b in zip(r, r[1:]))
    assert C.rating_a(replace(x, area_mm2=630, rho_soil=2.0))[0] < C.rating_a(replace(x, area_mm2=630))[0]


def test_fault_levels_pandapower_vs_independent():
    o = json.load(open(R / "faults.json"))
    assert o["worst_error_percent"] < 0.1


def test_pcc_grid_only_fault_equals_sk_over_root3_un():
    o = json.load(open(R / "faults.json"))
    pcc = [r for r in o["rows"] if r["bus"] == "PCC"][0]
    assert abs(pcc["max3_grid_only_ka"] - 10000 / (math.sqrt(3) * 400)) < 1e-6


def test_wind_contribution_is_arithmetic_sum_of_turbine_currents():
    o = json.load(open(R / "faults.json"))
    row = [r for r in o["rows"] if r["bus"] == "OSS66"][0]
    expect = 40 * 1.1 * 10 / (math.sqrt(3) * 66.0)
    assert abs((row["max3_total_ka"] - row["max3_grid_only_ka"]) - expect) < 0.01


def test_sk_curve_value():
    assert abs(G.t_op(10.0, 1.0, 1.0) - 0.14 / (10 ** 0.02 - 1)) < 1e-12


def test_grading_margins_recomputed_independently():
    g = json.load(open(R / "grading.json"))
    for loc, d in g["matrix"].items():
        for k, v in d.items():
            r = g["relays"][k]
            t = r["tms"] * 0.14 / ((v["i_a"] / r["pickup_a"]) ** 0.02 - 1)
            assert abs(t - v["t_s"]) < 1e-3
    for m in g["margins"]:
        d = g["matrix"][m["fault"]]
        assert d[m["up"]]["t_s"] - d[m["down"]]["t_s"] >= 0.30 - 1e-3
    for k, r in g["relays"].items():
        assert r["pickup_a"] >= 1.2 * r["load_a"]
        assert r["pickup_a"] <= 0.8 * r["zone_end_min_fault_a"]
    assert g["all_pass"]


def test_min_fault_ordering_finding_and_w3_clears_it():
    g = json.load(open(R / "grading.json"))["min_fault_check"]
    assert len(g["failing"]) == 1 and g["failing"][0]["down"] == "R3" and g["failing"][0]["up"] == "R4"
    assert g["w3_r4_tms_that_clears_min_fault"] == 0.35
    assert all(r["ok"] for r in g["w3_rows"])
