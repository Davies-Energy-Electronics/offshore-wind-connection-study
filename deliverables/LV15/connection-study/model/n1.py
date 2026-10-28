"""LV15: intact cases and N-1 on revision C, by the rules in criteria_C.json (written first). Writes results/n1.json and n1.txt."""
import json
import math
import warnings
from pathlib import Path

import revc
import build as B

warnings.filterwarnings("ignore")
R = Path(__file__).resolve().parents[1] / "results"
LIM = revc.CRIT["limits"]


def assess(net):
    """Exceptions list for a solved network: (kind, element, value). No solution is itself an exception."""
    if net is None:
        return [("no solution", "load flow did not converge", None)]
    ex = []
    for _, b in net.bus.iterrows():
        if b["name"] == "REM" or not b["in_service"]:
            continue
        v = net.res_bus.at[_, "vm_pu"]
        if math.isnan(v):
            continue
        lo, hi = LIM["voltage_pu"]["pcc_400kv"] if b["name"] == "PCC" else LIM["voltage_pu"]["internal_220kv_and_66kv"]
        if v < lo - 1e-9 or v > hi + 1e-9:
            ex.append(("voltage", b["name"], round(float(v), 4)))
    for _, l in net.line.iterrows():
        if l["in_service"] and l["name"] != "grid":
            ld = net.res_line.at[_, "loading_percent"]
            if ld > LIM["loading_percent"]["cables"] + 1e-9:
                ex.append(("loading", l["name"], round(float(ld), 2)))
    for _, t in net.trafo.iterrows():
        if t["in_service"]:
            ld = net.res_trafo.at[_, "loading_percent"]
            if ld > LIM["loading_percent"]["transformers"] + 1e-9:
                ex.append(("loading", t["name"], round(float(ld), 2)))
    return ex


NOSOLVE = []


def run(case, outage=None, scale=1.0):
    """Solved network, or None if the load flow does not converge (counted as outside limits)."""
    net = revc.build(case, outage, scale)
    try:
        B.solve_pp(net)
    except Exception:
        NOSOLVE.append((case["id"], outage, round(scale, 4)))
        return None
    return net


def summary(net):
    if net is None:
        return dict(gen_mw=None, to_grid_mw=None, loss_mw=None, bal_err_mw=None, pcc_pu=None, export_a=None, array_first_a=None,
                    max_line_loading=None, max_trafo_loading=None, vmax=None, vmin=None)
    n = net.line.name
    ok = net.line.in_service
    i = net.res_line.i_ka * 1000
    gen = float(net.res_sgen.p_mw[net.sgen.in_service].sum())
    grid = -float(net.res_ext_grid.p_mw.sum())
    loss = float(net.res_line.pl_mw[ok].sum() + net.res_trafo.pl_mw[net.trafo.in_service].sum())
    return dict(gen_mw=round(gen, 3), to_grid_mw=round(grid, 3), loss_mw=round(loss, 3), bal_err_mw=abs(gen - grid - loss),
                pcc_pu=round(float(net.res_bus.vm_pu[net.bus.name == "PCC"].iloc[0]), 4),
                export_a=round(float(i[n.str.startswith("EXP") & ok].max()), 1), array_first_a=round(float(i[n.str.match(r"A\d+_1$") & ok].max()), 1),
                max_line_loading=round(float(net.res_line.loading_percent[ok & (n != "grid")].max()), 1),
                max_trafo_loading=round(float(net.res_trafo.loading_percent[net.trafo.in_service].max()), 1),
                vmax=round(float(net.res_bus.vm_pu.max()), 4), vmin=round(float(net.res_bus.vm_pu.min()), 4))


def curtail(case, outage):
    """Largest scale (1 MW steps of total output) that is inside limits; voltage-only exceptions are not curable by curtailment."""
    p_full = case["p_mw"]
    lo, hi = 0.0, 1.0
    if assess(run(case, outage, 0.0)):
        return None
    while (hi - lo) * p_full > 1.0:
        mid = (lo + hi) / 2
        if assess(run(case, outage, mid)):
            hi = mid
        else:
            lo = mid
    return lo


def main():
    out = {"sized": revc.SIZED, "intact": {}, "n1": {}, "no_solution_runs": NOSOLVE}
    for c in revc.CASES:
        net = run(c)
        out["intact"][c["id"]] = dict(summary(net), exceptions=assess(net))
    for o in revc.CRIT["outages"]:
        out["n1"][o["id"]] = {"what": o["what"], "cases": {}}
        for c in revc.CASES:
            net = run(c, o["id"])
            ex = assess(net)
            row = dict(summary(net), exceptions=ex)
            if not ex:
                row["verdict"] = "RIDES THROUGH"
            elif all(k == "voltage" for k, _, _ in ex) and c["id"] == "C4":
                row["verdict"] = "VOLTAGE EXCEPTION (not curable by curtailment)"
            else:
                s = curtail(c, o["id"])
                if s is None:
                    row["verdict"] = "OUTSIDE LIMITS even at zero output"
                else:
                    inserv = 35 if o["id"] == "O4" else 40
                    row["verdict"] = "CURTAILED"
                    row["curtailed_mw"] = round(s * c["p_mw"] * inserv / 40, 1)
                    row["curtailed_summary"] = summary(run(c, o["id"], s))
            out["n1"][o["id"]]["cases"][c["id"]] = row
    json.dump(out, open(R / ("n1_D.json" if revc.REV == "D" else "n1.json"), "w"), indent=1)
    print(f"Revision {revc.REV} cables:", {k: (v["area_mm2"], round(v["rating_a"], 1)) for k, v in revc.SIZED.items()})
    print("\nINTACT")
    for k, v in out["intact"].items():
        print(k, {a: v[a] for a in ("gen_mw", "loss_mw", "pcc_pu", "export_a", "array_first_a", "max_line_loading", "max_trafo_loading", "vmax", "vmin")}, "exceptions", v["exceptions"])
    print("\nN-1")
    for o, d in out["n1"].items():
        print(o, d["what"])
        for k, v in d["cases"].items():
            extra = f" -> {v['curtailed_mw']} MW" if "curtailed_mw" in v else ""
            print("  ", k, v["verdict"] + extra, "| exceptions:", v["exceptions"][:4], "| export A", v["export_a"], "| max trafo %", v["max_trafo_loading"], "| PCC", v["pcc_pu"])


if __name__ == "__main__":
    main()
