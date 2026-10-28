"""Cable sizing run. Reads results/design_currents.json (revision B load flow) and writes results/cable_sizing.json."""
import json
from dataclasses import replace
from pathlib import Path

from cable import Inputs, rating_a, smallest, SERIES, parts

R = Path(__file__).resolve().parents[1] / "results"
dc = json.load(open(R / "design_currents.json"))
ARR = Inputs(un_kv=66.0, t_ins_mm=10.0)
EXP = Inputs(un_kv=220.0, t_ins_mm=24.0)
out = {"inputs": {"array": ARR.__dict__, "export": EXP.__dict__}}
for key, x, i_des in (("array", ARR, dc["array_first"]), ("export", EXP, dc["export"])):
    table = []
    for a in SERIES:
        i, p = rating_a(replace(x, area_mm2=a))
        table.append(dict(area=a, rating_a=round(i, 1), pct_of_design=round(100 * i_des / i, 1), R_ohm_km_90C=round(p["R_ohm_km"], 4),
                          c_nf_km=round(p["c_nf_per_km"], 1), d_ext_mm=round(p["d_ext_mm"], 1), ys=round(p["ys"], 4), yp=round(p["yp"], 4)))
    a, i, p = smallest(x, i_des)
    sens = {}
    for label, kw in (("soil 0.7", dict(rho_soil=0.7)), ("soil 1.5", dict(rho_soil=1.5)), ("soil 2.0", dict(rho_soil=2.0)), ("ambient 20", dict(theta_amb=20.0)),
                      ("lam 0", dict(lam=0.0)), ("lam 0.3", dict(lam=0.3)), ("depth 2 m", dict(depth_m=2.0))):
        sens[label] = round(rating_a(replace(x, area_mm2=a, **kw))[0], 1)
    # smallest size that still meets the design current under each sensitivity
    sens_size = {}
    for label, kw in (("soil 1.5", dict(rho_soil=1.5)), ("soil 2.0", dict(rho_soil=2.0)), ("lam 0.3", dict(lam=0.3))):
        sens_size[label] = smallest(replace(x, **kw), i_des)[0]
    out[key] = dict(design_a=round(i_des, 1), chosen_mm2=a, rating_a=round(i, 1), margin_pct=round(100 * (i / i_des - 1), 1), parts=p, table=table,
                    sensitivity_rating_at_chosen=sens, sensitivity_smallest_size=sens_size)
# N-1 informational: one export circuit carries both circuits' current
if True:
    ex = dc["export"]
    out["export"]["n1_informational_a"] = round(2 * ex, 1)
    out["export"]["n1_smallest_mm2"] = smallest(EXP, 2 * ex)[0]
json.dump(out, open(R / "cable_sizing.json", "w"), indent=1)
for k in ("array", "export"):
    o = out[k]
    print(k, "design", o["design_a"], "A -> chosen", o["chosen_mm2"], "mm2, rating", o["rating_a"], "A, margin", o["margin_pct"], "%")
    print("  parts", {a: round(b, 5) for a, b in o["parts"].items()})
    for r in o["table"]:
        print("   ", r)
    print("  sens rating", o["sensitivity_rating_at_chosen"], "sens size", o["sensitivity_smallest_size"])
print("N-1 info: single export circuit would need", out["export"]["n1_informational_a"], "A -> smallest", out["export"]["n1_smallest_mm2"], "mm2")
