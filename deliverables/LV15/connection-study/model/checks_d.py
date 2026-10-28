"""Checks of the final base design, revision D (criteria_D.json). Reads results/n1_D.json; writes results/checks_D.json."""
import json
import math
import os
import warnings
from pathlib import Path

os.environ["LV15_REV"] = "D"
import revc  # noqa: E402
import params as P  # noqa: E402
import faults as F  # noqa: E402

warnings.filterwarnings("ignore")
R = Path(__file__).resolve().parents[1] / "results"
D = json.load(open(R / "n1_D.json"))
G = json.load(open(revc.DEL / "LV14" / "connection-study" / "results" / "grading.json"))
out = {}
out["SOLVE"] = dict(result="FAIL" if D["no_solution_runs"] else "PASS", no_solution_runs=D["no_solution_runs"])
errs = [v["bal_err_mw"] for v in D["intact"].values()] + [r["bal_err_mw"] for o in D["n1"].values() for r in o["cases"].values() if r["bal_err_mw"] is not None]
out["BAL"] = dict(result="PASS" if max(errs) < 1e-6 else "FAIL", worst_mw=max(errs))
mw = D["n1"]["O2"]["cases"]["C1"]["curtailed_mw"]
out["HAND-O2"] = dict(result="PASS" if abs(mw / 250 - 1) <= 0.05 else "FAIL", curtailed_mw=mw, hand_mw=250.0, diff_pct=round(100 * abs(mw / 250 - 1), 2))
lv14 = {r["bus"]: r for r in json.load(open(revc.DEL / "LV14" / "connection-study" / "results" / "faults.json"))["rows"]}
exp = (P.EXP_R, P.EXP_X, P.EXP_C); arr = (P.ARR_R, P.ARR_X, P.ARR_C)
mx, _, _ = F.pp_faults("max", "3ph", F.SCL_MAX, True, exp=exp, arr=arr)
mn2, _, _ = F.pp_faults("min", "2ph", F.SCL_MIN, False, exp=exp, arr=arr)
rows = {n: dict(max3_revB=lv14[n]["max3_total_ka"], max3_revD=mx[n]["ikss_ka"], d_max_pct=100 * (mx[n]["ikss_ka"] / lv14[n]["max3_total_ka"] - 1),
                min2_revB=lv14[n]["min2_ka"], min2_revD=mn2[n]["ikss_ka"], d_min_pct=100 * (mn2[n]["ikss_ka"] / lv14[n]["min2_ka"] - 1)) for n in F.BUSES}
big = max(max(abs(r["d_max_pct"]), abs(r["d_min_pct"])) for r in rows.values())
out["FAULT-D"] = dict(result="PASS" if big <= 2 else "RE-CHECK GRADING", worst_change_pct=round(big, 3), rows=rows)
# R1 at 960 A (D7): pickup rule and margin to R2 at LV14's fault currents (fault change above is the reason they still apply)
K, A = 0.14, 0.02
t = lambda i, is_, tms: tms * K / ((i / is_) ** A - 1)
load = max(v["array_first_a"] for v in D["intact"].values())
zone_min = mn2["S1T8"]["ikss_ka"] * 1000
i_r1, i_r2, t_r2 = 16304.7, 6612.8, 0.6837          # LV14 results/grading.txt, fault F1 (string feeder end)
t1 = t(i_r1, 960.0, 0.100)
out["R1"] = dict(result="PASS" if (960 >= 1.2 * load and 960 <= 0.8 * zone_min and t_r2 - t1 >= 0.30) else "FAIL",
                 pickup_a=960.0, max_load_a=load, min_pickup_a=round(1.2 * load, 1), zone_end_min_fault_a=round(zone_min, 1), max_pickup_a=round(0.8 * zone_min, 1),
                 t_r1_s=round(t1, 4), t_r2_s=t_r2, margin_s=round(t_r2 - t1, 4), currents_source="LV14 results/grading.txt, F1")
json.dump(out, open(R / "checks_D.json", "w"), indent=1, default=str)
for k, v in out.items():
    print(k, v["result"], {a: b for a, b in v.items() if a not in ("result", "rows")})
for n, r in rows.items():
    print(f"   {n:7} max {r['max3_revB']:.3f} -> {r['max3_revD']:.3f} kA ({r['d_max_pct']:+.2f} %), min 2ph {r['min2_revB']:.3f} -> {r['min2_revD']:.3f} kA ({r['d_min_pct']:+.2f} %)")
