"""Overcurrent grading of the revision B base design, IEC standard inverse curves (constants NOT VERIFIED against IEC 60255-151).
Relay currents come from the grid-only impedance-matrix solution in faults.py; wind adds only to the string feeder relay R1.
Writes results/grading.json, results/grading_chart.png, results/grading_points.csv."""
import csv
import json
import math
import warnings
from pathlib import Path

import numpy as np

import faults as F
import revb

warnings.filterwarnings("ignore")
R = Path(__file__).resolve().parents[1] / "results"
K_SI, ALPHA = 0.14, 0.02
MARGIN_S = 0.30
PICKUP_LOAD, PICKUP_FAULT = 1.2, 0.8
TMS_STEPS = [round(0.025 * i, 3) for i in range(1, 41)]
R1_TMS = 0.100          # downstream-most relay: no margin rule applies; a design choice, not a result
K_CU = 143.0            # A sqrt(s) / mm2, copper XLPE, NOT SOURCED
WIND_PER_STRING_KA = F.P.N_TURB * F.K_WIND * F.P.P_TURB / (math.sqrt(3) * 66.0)


def t_op(i, is_, tms):
    x = i / is_
    return math.inf if x <= 1.0 else tms * K_SI / (x ** ALPHA - 1.0)


def loads():
    """Largest load current (A) over C1 to C4: string head, OSS transformer LV side, export circuit, onshore transformer HV side."""
    out = dict(R1=0.0, R2=0.0, R3=0.0, R4=0.0)
    for c in revb.CASES:
        net = revb.solve_case(c)
        i = net.res_line.i_ka * 1000
        n = net.line.name
        out["R1"] = max(out["R1"], i[n.str.match(r"A\d+_1$")].max())
        out["R3"] = max(out["R3"], i[n.str.startswith("EXP")].max())
        t = net.trafo.name
        out["R2"] = max(out["R2"], (net.res_trafo.i_lv_ka * 1000)[t.str.startswith("T_OSS")].max())
        out["R4"] = max(out["R4"], (net.res_trafo.i_hv_ka * 1000)[t.str.startswith("T_ON")].max())
    return out


def relay_currents(fault_bus, case, scl, three_phase=True, drop=()):
    """Primary current (A) each relay would see for a bolted fault at fault_bus, grid only."""
    b = F.branch_currents_ka(fault_bus, case, scl, three_phase, drop)
    return dict(R2=b["T_OSS1"][1] * 1000, R3=b["EXP1"][0] * 1000, R4=b["T_ON1"][0] * 1000,
                _grid_into_66=sum(b[n][1] for n in b if n.startswith("T_OSS")) * 1000)


def run():
    ld = loads()
    # fault locations: name -> bus and which relays can see it (forward looking only)
    maxf = {k: relay_currents(k, "max", F.SCL_MAX) for k in ("OSS66", "OSS220", "ON220")}
    r1_max = (maxf["OSS66"]["_grid_into_66"]) + (F.P.N_STRINGS - 1) * WIND_PER_STRING_KA * 1000   # fault just beyond a string breaker
    seen = {"F1 string feeder end (just beyond R1)": dict(R1=r1_max, R2=maxf["OSS66"]["R2"], R3=maxf["OSS66"]["R3"], R4=maxf["OSS66"]["R4"]),
            "F2 OSS 66 kV busbar": dict(R2=maxf["OSS66"]["R2"], R3=maxf["OSS66"]["R3"], R4=maxf["OSS66"]["R4"]),
            "F3 OSS 220 kV busbar": dict(R3=maxf["OSS220"]["R3"], R4=maxf["OSS220"]["R4"]),
            "F4 onshore 220 kV busbar": dict(R4=maxf["ON220"]["R4"])}
    # minimum fault at the far end of each relay's own zone (two-phase, minimum case, grid only)
    minb = {k: relay_currents(k, "min", F.SCL_MIN, three_phase=False) for k in ("OSS66", "OSS220", "ON220")}
    s1t8 = F.pp_faults("min", "2ph", F.SCL_MIN, False)[0]["S1T8"]["ikss_ka"] * 1000
    zone_min = dict(R1=s1t8, R2=minb["OSS66"]["R2"], R3=minb["OSS220"]["R3"], R4=minb["ON220"]["R4"])
    relays = {}
    for k in ("R1", "R2", "R3", "R4"):
        is_ = math.ceil(PICKUP_LOAD * ld[k] / 50.0) * 50.0
        relays[k] = dict(load_a=round(ld[k], 1), pickup_a=is_, zone_end_min_fault_a=round(zone_min[k], 1),
                         pickup_ok_load=bool(is_ >= PICKUP_LOAD * ld[k]), pickup_ok_fault=bool(is_ <= PICKUP_FAULT * zone_min[k]))
    names = {"R1": "string feeder breaker (66 kV)", "R2": "OSS transformer LV incomer (66 kV)", "R3": "export circuit, onshore end (220 kV)", "R4": "onshore transformer HV (400 kV)"}
    # TMS from downstream to upstream
    pairs = [("R1", "R2", "F1 string feeder end (just beyond R1)"), ("R2", "R3", "F2 OSS 66 kV busbar"), ("R3", "R4", "F3 OSS 220 kV busbar")]
    relays["R1"]["tms"] = R1_TMS
    for dn, up, loc in pairs:
        i_dn, i_up = seen[loc][dn], seen[loc][up]
        t_dn = t_op(i_dn, relays[dn]["pickup_a"], relays[dn]["tms"])
        pick = None
        for tms in TMS_STEPS:
            if t_op(i_up, relays[up]["pickup_a"], tms) - t_dn >= MARGIN_S:
                pick = tms
                break
        relays[up]["tms"] = pick
    for k, r in relays.items():
        r["name"] = names[k]
    # full matrix of operating times
    matrix = {}
    for loc, d in seen.items():
        matrix[loc] = {k: dict(i_a=round(i, 1), t_s=round(t_op(i, relays[k]["pickup_a"], relays[k]["tms"]), 4)) for k, i in d.items()}
    margins = []
    chain = ["R1", "R2", "R3", "R4"]
    for loc, d in matrix.items():
        ks = [k for k in chain if k in d]
        for a, b in zip(ks, ks[1:]):
            m = d[b]["t_s"] - d[a]["t_s"]
            margins.append(dict(fault=loc, down=a, up=b, margin_s=round(m, 4), ok=bool(m >= MARGIN_S - 1e-9)))
    # cable withstand
    sz = json.load(open(R / "cable_sizing.json"))
    wd = []
    arr_i = r1_max
    exp_i = F.pp_faults("max", "3ph", F.SCL_MAX, True)[0]["ON220"]["ikss_ka"] * 1000
    for lab, area, i_a, k_clear in (("array 630 mm2 (R1 clears)", sz["array"]["chosen_mm2"], arr_i, "R1"),
                                    ("export 500 mm2 (R3 clears, total fault at ON220 as bound)", sz["export"]["chosen_mm2"], exp_i, "R3")):
        t_allowed = (K_CU * area / i_a) ** 2
        i_relay = seen["F1 string feeder end (just beyond R1)"]["R1"] if k_clear == "R1" else maxf["OSS66"]["R3"]   # current the clearing relay sees
        t_clear = t_op(i_relay, relays[k_clear]["pickup_a"], relays[k_clear]["tms"])
        wd.append(dict(cable=lab, fault_a=round(i_a, 1), allowed_s=round(t_allowed, 2), relay_s=round(t_clear, 4), ok=bool(t_clear <= t_allowed),
                       min_area_mm2_for_relay_time=round(i_a * math.sqrt(t_clear) / K_CU, 1)))
    # informational: one OSS transformer out of service
    info = {}
    d1 = relay_currents("OSS66", "max", F.SCL_MAX, drop={"T_OSS2"})
    info["T_OSS2 out: R2 current at OSS66 busbar fault (A)"] = round(d1["R2"], 1)
    info["T_OSS2 out: R2 operating time (s)"] = round(t_op(d1["R2"], relays["R2"]["pickup_a"], relays["R2"]["tms"]), 4)
    # Added AFTER the chart was seen (not in criteria_B.json): ordering at the MINIMUM fault (two-phase, minimum case, no wind)
    bmin = {"string end S1T8 (just inside R1 zone end)": F.branch_currents_ka("S1T8", "min", F.SCL_MIN, False),
            "OSS 66 kV busbar": F.branch_currents_ka("OSS66", "min", F.SCL_MIN, False),
            "OSS 220 kV busbar": F.branch_currents_ka("OSS220", "min", F.SCL_MIN, False),
            "onshore 220 kV busbar": F.branch_currents_ka("ON220", "min", F.SCL_MIN, False)}

    def min_rows(tms_r4):
        rows = []
        for loc, b in bmin.items():
            cur = dict(R1=b["A1_1"][0] * 1000, R2=b["T_OSS1"][1] * 1000, R3=b["EXP1"][0] * 1000, R4=b["T_ON1"][0] * 1000)
            if not loc.startswith("string"):
                cur.pop("R1")
            tm = {k: relays[k]["tms"] for k in relays}
            tm["R4"] = tms_r4
            t = {k: t_op(i, relays[k]["pickup_a"], tm[k]) for k, i in cur.items() if i > relays[k]["pickup_a"]}
            ks = [k for k in chain if k in t]
            for a, c in zip(ks, ks[1:]):
                rows.append(dict(fault=loc, down=a, up=c, down_s=round(t[a], 3), up_s=round(t[c], 3), margin_s=round(t[c] - t[a], 3), ok=bool(t[c] - t[a] >= MARGIN_S - 1e-9)))
        return rows
    base_rows = min_rows(relays["R4"]["tms"])
    w3_tms = next((t for t in TMS_STEPS if all(r["ok"] for r in min_rows(t))), None)
    min_check = dict(rows=base_rows, failing=[r for r in base_rows if not r["ok"]], w3_r4_tms_that_clears_min_fault=w3_tms,
                     w3_rows=min_rows(w3_tms) if w3_tms else None)
    out = dict(curve=dict(k=K_SI, alpha=ALPHA, margin_s=MARGIN_S, pickup_load_factor=PICKUP_LOAD, pickup_fault_factor=PICKUP_FAULT, r1_tms_choice=R1_TMS),
               wind_per_string_ka=WIND_PER_STRING_KA, relays=relays, matrix=matrix, margins=margins, withstand=wd, informational=info, min_fault_check=min_check,
               all_pass=bool(all(m["ok"] for m in margins) and all(r["pickup_ok_load"] and r["pickup_ok_fault"] for r in relays.values()) and all(w["ok"] for w in wd) and all(r["tms"] for r in relays.values())))
    json.dump(out, open(R / "grading.json", "w"), indent=1)
    chart(relays, seen)
    return out


def chart(relays, seen):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ref = {"R1": 1.0, "R2": 1.0, "R3": 220.0 / 66.0, "R4": 400.0 / 66.0}   # multiply primary A to refer to 66 kV
    cols = {"R1": "#1b6ca8", "R2": "#c0392b", "R3": "#27ae60", "R4": "#8e44ad"}
    fig, ax = plt.subplots(figsize=(10, 6.5))
    rows = [("relay", "current_66kV_ref_a", "time_s")]
    for k, r in relays.items():
        lo = r["pickup_a"] * 1.05
        xs = np.geomspace(lo, 40000.0 / ref[k], 200)
        ts = [t_op(x, r["pickup_a"], r["tms"]) for x in xs]
        ax.plot(xs * ref[k], ts, color=cols[k], lw=2, label=f"{k} {r['name']}: Is {r['pickup_a']:.0f} A, TMS {r['tms']}")
        rows += [(k, round(x * ref[k], 1), round(t, 4)) for x, t in zip(xs[::20], ts[::20])]
    for loc, d in seen.items():
        for k, i in d.items():
            t = t_op(i, relays[k]["pickup_a"], relays[k]["tms"])
            ax.plot(i * ref[k], t, "o", color=cols[k], ms=6)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(500, 40000); ax.set_ylim(0.05, 20)
    ax.set_xlabel("Fault current referred to 66 kV (A)"); ax.set_ylabel("Operating time (s)")
    ax.set_title("LV14 overcurrent grading, revision B base design\nSELF-DIRECTED STUDY, ASSUMED DATA. Dots are the fault cases in grading.json", fontsize=10)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(R / "grading_chart.png", dpi=130)
    with open(R / "grading_points.csv", "w", newline="") as f:
        csv.writer(f).writerows(rows)


if __name__ == "__main__":
    o = run()
    print("curve", o["curve"], "wind per string kA", round(o["wind_per_string_ka"], 3))
    for k, r in o["relays"].items():
        print(k, r)
    for loc, d in o["matrix"].items():
        print(loc, d)
    for m in o["margins"]:
        print(m)
    for w in o["withstand"]:
        print(w)
    print(o["informational"])
    mc = o["min_fault_check"]
    for r in mc["rows"]:
        print("MIN", r)
    print("MIN failing", len(mc["failing"]), "W3 R4 TMS", mc["w3_r4_tms_that_clears_min_fault"])
    for r in (mc["w3_rows"] or []):
        print("W3", r)
    print("ALL PASS", o["all_pass"])
