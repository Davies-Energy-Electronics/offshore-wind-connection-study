"""What-if W2 (informational, not part of the pass rule): LV13 revision B re-run with the export and array cable
resistance, charging capacitance and rating replaced by the sized values from cable_sizing.json. Reactance and lengths unchanged.
Chosen after the sizing was seen, so it is a consistency check on the base design, not a result of it."""
import json
import warnings
from pathlib import Path

import revb
import params as P

warnings.filterwarnings("ignore")
R = Path(__file__).resolve().parents[1] / "results"
sz = json.load(open(R / "cable_sizing.json"))
ex, ar = sz["export"], sz["array"]
base = (P.EXP_R, P.EXP_C, P.EXP_IMAX_KA, P.ARR_R, P.ARR_C, P.ARR_IMAX_KA)
P.EXP_R, P.EXP_C, P.EXP_IMAX_KA = ex["parts"]["R_ohm_km"], ex["parts"]["c_nf_per_km"], ex["rating_a"] / 1000
P.ARR_R, P.ARR_C, P.ARR_IMAX_KA = ar["parts"]["R_ohm_km"], ar["parts"]["c_nf_per_km"], ar["rating_a"] / 1000
out = {"inputs": dict(exp_r=P.EXP_R, exp_c=P.EXP_C, exp_rating_a=ex["rating_a"], arr_r=P.ARR_R, arr_c=P.ARR_C, arr_rating_a=ar["rating_a"],
                      LV13_exp=(base[0], base[1], base[2] * 1000), LV13_arr=(base[3], base[4], base[5] * 1000)), "cases": {}}
for c in revb.CASES:
    net = revb.solve_case(c)
    n = net.line.name
    i = net.res_line.i_ka * 1000
    pcc = float(net.res_bus.vm_pu[net.bus.name == "PCC"].iloc[0])
    load = net.res_line.loading_percent
    out["cases"][c["id"]] = dict(array_first_a=float(i[n.str.match(r"A\d+_1$")].max()), export_a=float(i[n.str.startswith("EXP")].max()),
                                 array_loading_pct=float(load[n.str.startswith("A")].max()), export_loading_pct=float(load[n.str.startswith("EXP")].max()),
                                 pcc_pu=pcc, max_bus_pu=float(net.res_bus.vm_pu.max()), min_bus_pu=float(net.res_bus.vm_pu.min()),
                                 loss_mw=float(net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum()))
json.dump(out, open(R / "whatif_w2.json", "w"), indent=1)
print(json.dumps(out, indent=1))
