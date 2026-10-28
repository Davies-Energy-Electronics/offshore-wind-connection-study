"""LV15 checks (criteria_C.json) and labelled what-ifs. Reads results/n1.json; writes results/checks.json; prints checks.txt."""
import json
import math
import warnings
from dataclasses import replace
from pathlib import Path

import revc
import params as P
import build as B
from n1 import run, assess, summary
from cable import rating_a
import faults as F

warnings.filterwarnings("ignore")
R = Path(__file__).resolve().parents[1] / "results"
D = json.load(open(R / "n1.json"))
CASE = {c["id"]: c for c in revc.CASES}
out = {}

# SOLVE: every run converges
out["SOLVE"] = dict(result="FAIL" if D["no_solution_runs"] else "PASS", no_solution_runs=D["no_solution_runs"],
                    note="A run that does not converge is counted as outside limits in the N-1 table; the criteria asked for every run to converge, so this is reported as a finding.")

# BAL: energy balance on every intact and full-output N-1 run that solved
errs = [v["bal_err_mw"] for v in D["intact"].values()] + [r["bal_err_mw"] for o in D["n1"].values() for r in o["cases"].values() if r["bal_err_mw"] is not None]
out["BAL"] = dict(result="PASS" if max(errs) < 1e-6 else "FAIL", worst_mw=max(errs))

# HAND-O1: with EXP1 out at C1, EXP2 current against the intact two-circuit total
ia = D["intact"]["C1"]["export_a"]; io = D["n1"]["O1"]["cases"]["C1"]["export_a"]
d1 = 100 * abs(io / (2 * ia) - 1)
# refined hand check: split the intact current into its in-phase part (from active power, unchanged) and the
# charging part of the circuit that is out (half the total charging leaves with it)
v_kv = 220.0 * 1.0
p_mw = D["intact"]["C1"]["gen_mw"] - D["intact"]["C1"]["loss_mw"] / 2
i_p = p_mw * 1e3 / (math.sqrt(3) * v_kv)                                  # A, both circuits together, active part
q_ch = v_kv ** 2 * 2 * math.pi * 50 * P.EXP_C * 1e-9 * P.LEN_EXP          # MVAr per circuit at 220 kV
i_c1 = q_ch * 1e3 / (math.sqrt(3) * v_kv)                                 # A per circuit, charging (whole length)
i_hand = math.hypot(i_p, i_c1 / 2)                                        # sending end of one circuit, charging split half each end
out["HAND-O1"] = dict(result="PASS" if d1 <= 5 else "FAIL", intact_per_circuit_a=ia, outage_a=io, simple_rule_diff_pct=round(d1, 2),
                      note="The 5 percent rule in the criteria assumed the remaining circuit carries the intact total. It does not: half the cable charging current leaves with the circuit that is out. Refined hand value shown for information.",
                      refined_hand_a=round(i_hand, 1), refined_diff_pct=round(100 * abs(io / i_hand - 1), 2))

# HAND-O2: curtailed output with one 250 MVA OSS transformer out at C1, against 250 MVA x pf minus array losses
r2 = D["n1"]["O2"]["cases"]["C1"]
cs = r2["curtailed_summary"]
arr_loss = cs["loss_mw"]
hand = 250.0 * 1.0 + 0.0      # unity power factor at the turbines; transformer limit on its own MVA
d2 = 100 * abs(r2["curtailed_mw"] / hand - 1)
out["HAND-O2"] = dict(result="PASS" if d2 <= 5 else "FAIL", curtailed_mw=r2["curtailed_mw"], hand_mw=hand, diff_pct=round(d2, 2),
                      note="Hand value: the remaining 250 MVA transformer at full loading, unity power factor; array charging and losses explain the difference.")

# FAULT-C: maximum fault levels on revision C cables against LV14 (revision B cables)
lv14 = {r["bus"]: r for r in json.load(open(revc.DEL / "LV14" / "connection-study" / "results" / "faults.json"))["rows"]}
exp = (P.EXP_R, P.EXP_X, P.EXP_C); arr = (P.ARR_R, P.ARR_X, P.ARR_C)
mx, _, _ = F.pp_faults("max", "3ph", F.SCL_MAX, True, exp=exp, arr=arr)
mn2, _, _ = F.pp_faults("min", "2ph", F.SCL_MIN, False, exp=exp, arr=arr)
rows = {}
for n in F.BUSES:
    rows[n] = dict(max3_revB=lv14[n]["max3_total_ka"], max3_revC=mx[n]["ikss_ka"], d_max_pct=100 * (mx[n]["ikss_ka"] / lv14[n]["max3_total_ka"] - 1),
                   min2_revB=lv14[n]["min2_ka"], min2_revC=mn2[n]["ikss_ka"], d_min_pct=100 * (mn2[n]["ikss_ka"] / lv14[n]["min2_ka"] - 1))
big = max(max(abs(r["d_max_pct"]), abs(r["d_min_pct"])) for r in rows.values())
out["FAULT-C"] = dict(result="PASS" if big <= 2 else "RE-CHECK GRADING", worst_change_pct=round(big, 2), rows=rows,
                      note="LV14 used LV13's cable impedances (decision recorded there). If no busbar moves by more than 2 percent, LV14's grading verdicts stand for revision C.")

# what-if W3 (labelled, not part of the base): the array re-sized on the revision C design current
i_des = max(v["array_first_a"] for v in D["intact"].values())
arr_ok = None
for a in (1000, 1200):
    i, p = rating_a(replace(revc.ARR, area_mm2=a))
    if i >= i_des:
        arr_ok = (a, i, p); break
a, i, p = arr_ok
base = (P.ARR_R, P.ARR_C, P.ARR_IMAX_KA)
P.ARR_R, P.ARR_C, P.ARR_IMAX_KA = p["R_ohm_km"], p["c_nf_per_km"], i / 1000
w3 = {}
for cid in ("C1", "C2", "C3", "C4"):
    net = run(CASE[cid]); w3[cid] = dict(summary(net), exceptions=assess(net))
P.ARR_R, P.ARR_C, P.ARR_IMAX_KA = base
out["W3"] = dict(what=f"array re-sized on the revision C design current {i_des:.1f} A at soil 1.5: {a} mm2, rating {i:.1f} A", cases=w3,
                 note="Chosen after seeing the C3 exception; informational. Shows the sizing has to be iterated: a bigger cable has more charging current.")

# what-if W4 (labelled): the 310 MVAr reactor split into two 155 MVAr units, one out
w4 = {}
for cid in ("C1", "C2", "C3", "C4"):
    net = revc.build(CASE[cid], None, 1.0, reactor=155.0)
    try:
        B.solve_pp(net); w4[cid] = dict(summary(net), exceptions=assess(net))
    except Exception:
        w4[cid] = dict(exceptions=[("no solution", "", None)])
out["W4"] = dict(what="onshore reactor as two 155 MVAr units, one out (half the compensation left)", cases=w4)

json.dump(out, open(R / "checks.json", "w"), indent=1, default=str)
for k in ("SOLVE", "BAL", "HAND-O1", "HAND-O2", "FAULT-C"):
    v = out[k]; print(k, v["result"], {a: b for a, b in v.items() if a not in ("result", "rows", "note")})
    if "note" in v: print("   ", v["note"])
for n, r in rows.items():
    print(f"   {n:7} max {r['max3_revB']:.3f} -> {r['max3_revC']:.3f} kA ({r['d_max_pct']:+.2f} %), min 2ph {r['min2_revB']:.3f} -> {r['min2_revC']:.3f} kA ({r['d_min_pct']:+.2f} %)")
for k in ("W3", "W4"):
    print(k, out[k]["what"])
    for cid, v in out[k]["cases"].items():
        print("   ", cid, "exceptions", v["exceptions"][:4], "| max line %", v.get("max_line_loading"), "| vmax", v.get("vmax"), "| PCC", v.get("pcc_pu"))
