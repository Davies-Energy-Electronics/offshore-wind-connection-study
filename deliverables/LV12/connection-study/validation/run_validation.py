"""Validate pandapower against (1) the published IEEE solution where one was read, (2) an independent
Newton-Raphson solver and (3) pandapower's own bundled case. Tolerances come from validation/criteria.json,
which was committed before the first run.

    python3 casefiles/fetch_data.py && python3 validation/run_validation.py

Writes results/validation_results.json and one CSV of bus results per case. Exit 0 only if every check
without a status passed.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandapower as pp
import pandapower.networks as pn
from pandapower.converter.pypower.from_ppc import from_ppc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import independent_nr  # noqa: E402
import mpc  # noqa: E402

CRITERIA = json.loads((HERE / "criteria.json").read_text())
TOL = {c["id"]: c for c in CRITERIA["checks"]}
PLACEHOLDER_KV = 132.0  # case14.m carries no base kV; per-unit results do not depend on this value
RUN_KW = dict(algorithm="nr", init="flat", tolerance_mva=1e-9, max_iteration=50, enforce_q_lims=False,
              calculate_voltage_angles=True)


def build_net(case):
    bus = case["bus"].copy()
    bus[bus[:, mpc.BASE_KV] == 0, mpc.BASE_KV] = PLACEHOLDER_KV
    ppc = {"version": "2", "baseMVA": case["baseMVA"], "bus": bus, "gen": case["gen"], "branch": case["branch"]}
    return from_ppc(ppc, f_hz=60 if case["baseMVA"] == 100 and bus[0, mpc.BASE_KV] == 345 else 50)


def pandapower_results(net, case):
    pp.runpp(net, **RUN_KW)
    nums = case["bus"][:, mpc.BUS_I].astype(int)
    vm = net.res_bus.loc[nums, "vm_pu"].to_numpy()
    va = net.res_bus.loc[nums, "va_degree"].to_numpy()
    ends = {}
    for _, r in net.res_line.join(net.line[["from_bus", "to_bus"]]).iterrows():
        ends[(int(r.from_bus), int(r.to_bus))] = (r.p_from_mw, r.q_from_mvar)
        ends[(int(r.to_bus), int(r.from_bus))] = (r.p_to_mw, r.q_to_mvar)
    for _, r in net.res_trafo.join(net.trafo[["hv_bus", "lv_bus"]]).iterrows():
        ends[(int(r.hv_bus), int(r.lv_bus))] = (r.p_hv_mw, r.q_hv_mvar)
        ends[(int(r.lv_bus), int(r.hv_bus))] = (r.p_lv_mw, r.q_lv_mvar)
    f = case["branch"][:, mpc.F_BUS].astype(int)
    t = case["branch"][:, mpc.T_BUS].astype(int)
    flows = np.array([[*ends[(a, b)], *ends[(b, a)]] for a, b in zip(f, t)])
    gen_p = np.zeros(len(nums))
    gen_q = np.zeros(len(nums))
    pos = {n: i for i, n in enumerate(nums)}
    slack = net.res_ext_grid
    for _, r in net.ext_grid.iterrows():
        gen_p[pos[int(r.bus)]] += slack.loc[_, "p_mw"]
        gen_q[pos[int(r.bus)]] += slack.loc[_, "q_mvar"]
    for i, r in net.gen.iterrows():
        gen_p[pos[int(r.bus)]] += net.res_gen.loc[i, "p_mw"]
        gen_q[pos[int(r.bus)]] += net.res_gen.loc[i, "q_mvar"]
    loss = float(net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum())
    return {"vm": vm, "va_deg": va, "pf": flows[:, 0], "qf": flows[:, 1], "pt": flows[:, 2], "qt": flows[:, 3],
            "gen_p": gen_p, "gen_q": gen_q, "loss_mw": loss, "bus_numbers": nums}


def worst(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def record(out, cid, case, measured, unit, extra=""):
    c = TOL[cid]
    tol = c.get("tolerance")
    status = c.get("status")
    if status:
        verdict = status
    else:
        verdict = "PASS" if measured <= tol else "FAIL"
    out.append({"check": cid, "case": case, "quantity": c.get("quantity", ""), "max_abs_deviation": measured,
                "unit": unit, "tolerance": tol, "verdict": verdict, "detail": extra})


def published_14(case, r):
    """The published IEEE 14-bus solution as printed in the Vm, Va, Pg and Qg columns of case14.m."""
    bus, gen = case["bus"], case["gen"]
    out = []
    nums = bus[:, mpc.BUS_I].astype(int)
    pub_vm, pub_va = bus[:, mpc.VM], bus[:, mpc.VA]
    gbus = gen[:, mpc.GEN_BUS].astype(int)
    pos = {n: i for i, n in enumerate(nums)}
    gi = [pos[b] for b in gbus]
    record(out, "C14-PUB-VM", "case14", worst(r["vm"], pub_vm), "pu")
    record(out, "C14-PUB-VA", "case14", worst(r["va_deg"], pub_va), "degree")
    record(out, "C14-PUB-QG", "case14", worst(r["gen_q"][gi], gen[:, mpc.QG]), "MVAr")
    slack_i = int(np.where(bus[:, mpc.BUS_TYPE] == mpc.REF)[0][0])
    pub_pg_slack = gen[gen[:, mpc.GEN_BUS] == bus[slack_i, mpc.BUS_I], mpc.PG][0]
    record(out, "C14-PUB-PG", "case14", abs(r["gen_p"][slack_i] - pub_pg_slack), "MW")
    pub_loss = gen[:, mpc.PG].sum() - bus[:, mpc.PD].sum()
    record(out, "C14-PUB-LOSS", "case14", abs(r["loss_mw"] - pub_loss), "MW", f"published loss {pub_loss:.3f} MW")
    return out


def informational_9(case, r):
    gen = case["gen"]
    nums = case["bus"][:, mpc.BUS_I].astype(int)
    pos = {n: i for i, n in enumerate(nums)}
    gi = [pos[int(b)] for b in gen[:, mpc.GEN_BUS]]
    out = []
    record(out, "C9-CHOW-QG", "case9", worst(r["gen_q"][gi], gen[:, mpc.QG]), "MVAr")
    slack_i = int(np.where(case["bus"][:, mpc.BUS_TYPE] == mpc.REF)[0][0])
    record(out, "C9-CHOW-PG1", "case9", abs(r["gen_p"][slack_i] - gen[0, mpc.PG]), "MW",
           f"case file {gen[0, mpc.PG]} MW, pandapower {r['gen_p'][slack_i]:.3f} MW")
    return out


def published_9_table(case, r):
    p = ROOT.parent.parent.parent / "inputs" / "LV12" / "case9_published.csv"
    if not p.exists():
        return []
    rows = [x for x in csv.DictReader(p.open()) if not str(next(iter(x.values()), "")).startswith("#")]
    # columns: bus (MATPOWER numbering) or wscc_bus (the textbook's numbering), vm_pu, va_degree.
    # WSCC to MATPOWER, mapped by load (125 MW at WSCC 5 = MATPOWER 9; 90 MW at 6 = 5; 100 MW at 8 = 7), not by result.
    W2M = {1: 1, 2: 2, 3: 3, 4: 4, 5: 9, 6: 5, 7: 8, 8: 7, 9: 6}
    key = "wscc_bus" if rows and "wscc_bus" in rows[0] else "bus"
    pub = {(W2M[int(x[key])] if key == "wscc_bus" else int(x[key])): (float(x["vm_pu"]), float(x["va_degree"]))
           for x in rows if x.get("vm_pu") and x.get("va_degree")}
    if len(pub) < 9:
        return []
    nums = r["bus_numbers"]
    vm = worst([r["vm"][i] for i, n in enumerate(nums) if n in pub], [pub[n][0] for n in nums if n in pub])
    va = worst([r["va_deg"][i] for i, n in enumerate(nums) if n in pub], [pub[n][1] for n in nums if n in pub])
    return [{"check": "C9-PUB-VM", "case": "case9", "quantity": "bus voltage magnitude", "max_abs_deviation": vm, "unit": "pu",
             "tolerance": 0.001, "verdict": "PASS" if vm <= 0.001 else "FAIL", "detail": str(p)},
            {"check": "C9-PUB-VA", "case": "case9", "quantity": "bus voltage angle", "max_abs_deviation": va, "unit": "degree",
             "tolerance": 0.05, "verdict": "PASS" if va <= 0.05 else "FAIL", "detail": str(p)}]


def cross_checks(name, r, ind, out):
    record(out, "X-VM", name, worst(r["vm"], ind["vm"]), "pu")
    record(out, "X-VA", name, worst(r["va_deg"], ind["va_deg"]), "degree")
    flow = max(worst(r[k], ind[k]) for k in ("pf", "qf", "pt", "qt"))
    record(out, "X-FLOW", name, flow, "MW or MVAr")
    record(out, "X-LOSS", name, abs(r["loss_mw"] - ind["loss_mw"]), "MW")


def bundled_check(name, bundled, r, case, out):
    pp.runpp(bundled, **RUN_KW)
    nums = case["bus"][:, mpc.BUS_I].astype(int)
    # the bundled nets are indexed from 0, in case-file order
    vm = bundled.res_bus.vm_pu.to_numpy()
    va = bundled.res_bus.va_degree.to_numpy()
    dvm, dva = worst(vm, r["vm"]), worst(va, r["va_deg"])
    c = TOL["D-BUNDLED"]
    out.append({"check": "D-BUNDLED", "case": name, "quantity": c["quantity"], "max_abs_deviation": dva,
                "unit": "degree", "tolerance": None, "verdict": "PASS" if dvm <= c["tolerance_vm"] and dva <= c["tolerance_va"] else "FAIL",
                "detail": f"max |dVm| {dvm:.3e} pu, max |dVa| {dva:.3e} degree"})


def write_bus_csv(name, case, r, ind):
    path = ROOT / "results" / f"{name}_bus_results.csv"
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["bus", "pandapower_vm_pu", "independent_vm_pu", "pandapower_va_deg", "independent_va_deg"])
        for i, n in enumerate(r["bus_numbers"]):
            w.writerow([int(n), f"{r['vm'][i]:.8f}", f"{ind['vm'][i]:.8f}", f"{r['va_deg'][i]:.6f}", f"{ind['va_deg'][i]:.6f}"])


def main():
    (ROOT / "results").mkdir(exist_ok=True)
    results, meta = [], {"pandapower_version": pp.__version__, "numpy_version": np.__version__,
                         "criteria_revision": CRITERIA["revision"], "cases": {}}
    for name, bundled in (("case9", pn.case9), ("case14", pn.case14)):
        case = mpc.read_case(ROOT / "casefiles" / f"{name}.m")
        net = build_net(case)
        r = pandapower_results(net, case)
        ind = independent_nr.solve(case)
        meta["cases"][name] = {"buses": int(len(case["bus"])), "branches": int(len(case["branch"])),
                               "independent_iterations": ind["iterations"], "loss_mw_pandapower": r["loss_mw"],
                               "loss_mw_independent": ind["loss_mw"]}
        cross_checks(name, r, ind, results)
        bundled_check(name, bundled(), r, case, results)
        if name == "case14":
            results += published_14(case, r)
        else:
            results += informational_9(case, r)
            results += published_9_table(case, r)
            if not any(x["check"].startswith("C9-PUB") for x in results):
                c = TOL["C9-PUB"]
                results.append({"check": "C9-PUB", "case": name, "quantity": "published solution table", "max_abs_deviation": None,
                                "unit": "", "tolerance": None, "verdict": c["status"], "detail": "NOT SOURCED: " + c["reason"]})
        write_bus_csv(name, case, r, ind)
    (ROOT / "results" / "validation_results.json").write_text(json.dumps({"meta": meta, "checks": results}, indent=1))
    for x in results:
        dev = "-" if x["max_abs_deviation"] is None else f"{x['max_abs_deviation']:.3e}"
        print(f"{x['verdict']:13s} {x['check']:14s} {x['case']:7s} dev {dev:>10s} {x['unit']:12s} tol {x['tolerance']}  {x['detail'][:60]}")
    failed = [x for x in results if x["verdict"] == "FAIL"]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
