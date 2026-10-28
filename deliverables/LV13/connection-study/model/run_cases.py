"""Solve the four cases with pandapower and write results/cases.json and results/cases.md."""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B  # noqa: E402
import params as P  # noqa: E402

CRIT = json.loads((HERE / "criteria.json").read_text())
VL = CRIT["voltage_limits_pu"]


def vlimit(name):
    return VL["pcc_400kv"] if name == "PCC" else VL["internal_220kv_and_66kv"]


def trafo_loading(net, i):
    """Apparent power over nameplate MVA, worst end (criteria.json). pandapower's own loading_percent for a
    transformer is current over rated current, which reads lower than this when the voltage is above 1 pu."""
    t, rr = net.trafo, net.res_trafo
    s = max(math.hypot(rr.p_hv_mw[i], rr.q_hv_mvar[i]), math.hypot(rr.p_lv_mw[i], rr.q_lv_mvar[i]))
    return s / t.sn_mva[i] * 100


def evaluate(net, case):
    """Return a dict of results and the list of exceptions for one solved case."""
    bus = net.bus
    vm = net.res_bus.vm_pu
    exc = []
    worst_v = {}
    bad = {}
    for i, n in bus.name.items():
        lo, hi = vlimit(n)
        if vm[i] < lo or vm[i] > hi:
            key = "PCC" if n == "PCC" else ("66 kV array" if n.startswith("S") else n)
            bad.setdefault(key, []).append((n, float(vm[i]), lo, hi))
    for key, items in bad.items():
        vs = [x[1] for x in items]
        exc.append(f"voltage {key}: {len(items)} bus(es), {min(vs):.4f} to {max(vs):.4f} pu, limits [{items[0][2]}, {items[0][3]}]")
    groups = {"PCC 400 kV": ["PCC"], "220 kV buses": ["ON220", "OSS220"], "66 kV OSS": ["OSS66"], "66 kV array": [n for n in bus.name if n.startswith("S")]}
    for g, ns in groups.items():
        vals = {n: float(vm[bus.index[bus.name == n][0]]) for n in ns}
        mx, mn = max(vals, key=vals.get), min(vals, key=vals.get)
        worst_v[g] = {"max": vals[mx], "max_bus": mx, "min": vals[mn], "min_bus": mn}
    loads = {}
    for i, n in net.line.name.items():
        if n == "grid":
            continue
        loads[n] = float(net.res_line.loading_percent[i])
    for i, n in net.trafo.name.items():
        loads[n] = trafo_loading(net, i)
    for n, v in loads.items():
        lim = CRIT["loading_limit_percent"]["transformers" if n.startswith("T_") else "cables"]
        if v > lim:
            exc.append(f"loading {n} = {v:.2f} percent above {lim}")
    pcc_i = net.line.index[net.line.name == "grid"][0]
    gen_p = float(net.sgen.p_mw.sum())
    gen_q = float(net.sgen.q_mvar.sum())
    loss = float(net.res_line.pl_mw.sum() - net.res_line.pl_mw[pcc_i] + net.res_trafo.pl_mw.sum())  # farm and export losses, grid impedance excluded
    arr = [v for n, v in loads.items() if n.startswith("A")]
    return {
        "converged": bool(net.converged), "gen_p_mw": gen_p, "gen_q_mvar": gen_q,
        "p_pcc_to_grid_mw": float(net.res_line.p_to_mw[pcc_i]),
        "q_pcc_to_grid_mvar": float(net.res_line.q_to_mvar[pcc_i]),
        "loss_mw": loss, "voltage": worst_v, "loading_max": {"array": max(arr), "export": max(v for n, v in loads.items() if n.startswith("EXP")),
        "oss_trafo": max(v for n, v in loads.items() if n.startswith("T_OSS")), "onshore_trafo": max(v for n, v in loads.items() if n.startswith("T_ON"))},
        "pandapower_trafo_loading_percent": {n: float(net.res_trafo.loading_percent[i]) for i, n in net.trafo.name.items()}, "loadings": loads, "bus_vm": {n: float(vm[i]) for i, n in bus.name.items()}, "exceptions": exc,
    }


def run_all(scl=P.SCL_MVA, exp_c=P.EXP_C, reactor=None):
    out = {}
    for case in CRIT["cases"]:
        net = B.solve_pp(B.build_pp(case, scl, exp_c, reactor))
        out[case["id"]] = evaluate(net, case)
    return out


def main():
    res = run_all()
    import pandapower
    meta = {"pandapower": pandapower.__version__, "reactor_mvar": P.reactor_mvar()}
    (HERE.parent / "results").mkdir(exist_ok=True)
    (HERE.parent / "results" / "cases.json").write_text(json.dumps({"meta": meta, "cases": res}, indent=1))
    lines = ["| Case | P gen (MW) | Q gen (MVAr) | P into grid (MW) | Q into grid (MVAr) | Loss (MW) | PCC V (pu) | Max 220 kV V (pu) | Max 66 kV V (pu) | Min 66 kV V (pu) | Array cable (%) | Export cable (%) | OSS trafo (%) | Onshore trafo (%) | Verdict |",
             "|" + "---|" * 15]
    for c in CRIT["cases"]:
        r = res[c["id"]]
        v, l = r["voltage"], r["loading_max"]
        v66 = [v["66 kV OSS"]["max"], v["66 kV array"]["max"]]
        v66min = [v["66 kV OSS"]["min"], v["66 kV array"]["min"]]
        lines.append(f"| {c['id']} | {r['gen_p_mw']:.1f} | {r['gen_q_mvar']:.1f} | {r['p_pcc_to_grid_mw']:.2f} | {r['q_pcc_to_grid_mvar']:.2f} | {r['loss_mw']:.2f} | {v['PCC 400 kV']['max']:.4f} | {v['220 kV buses']['max']:.4f} | {max(v66):.4f} | {min(v66min):.4f} | {l['array']:.1f} | {l['export']:.1f} | {l['oss_trafo']:.1f} | {l['onshore_trafo']:.1f} | {'INSIDE LIMITS' if r['converged'] and not r['exceptions'] else 'EXCEPTIONS (' + str(len(r['exceptions'])) + ')'} |")
    lines.append("")
    for c in CRIT["cases"]:
        r = res[c["id"]]
        for e in r["exceptions"]:
            lines.append(f"- {c['id']}: {e}")
    (HERE.parent / "results" / "cases.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
