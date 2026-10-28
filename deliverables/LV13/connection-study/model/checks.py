"""Independent check of the four cases: second solver, energy balance, hand-style formulae.
Writes results/checks.txt and results/checks.json."""
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B  # noqa: E402
from run_cases import trafo_loading  # noqa: E402
import params as P  # noqa: E402
import independent_nr as NR  # noqa: E402

CRIT = json.loads((HERE / "criteria.json").read_text())
TOL = {c["id"]: c["tolerance"] for c in CRIT["checks"]}


def independent(case, **kw):
    """Solve with pandapower and with the independent solver; return worst differences."""
    net = B.solve_pp(B.build_pp(case, **kw))
    mpc, names, br, buses = B.build_mpc(case, **kw)
    r = NR.solve(mpc)
    vm_pp = np.array([net.res_bus.vm_pu[net.bus.index[net.bus.name == n][0]] for n in names])
    va_pp = np.array([net.res_bus.va_degree[net.bus.index[net.bus.name == n][0]] for n in names])
    d_vm = float(np.max(np.abs(vm_pp - r["vm"])))
    d_va = float(np.max(np.abs(va_pp - r["va_deg"])))
    d_flow, d_load = 0.0, 0.0
    for k, b in enumerate(br):
        if b["kind"] == "line":
            i = net.line.index[net.line.name == b["name"]][0]
            rr = net.res_line
            pp_vals = [rr.p_from_mw[i], rr.q_from_mvar[i], rr.p_to_mw[i], rr.q_to_mvar[i]]
            load_pp = rr.loading_percent[i]
            imax = b["imax_ka"]
        else:
            i = net.trafo.index[net.trafo.name == b["name"]][0]
            rr = net.res_trafo
            pp_vals = [rr.p_hv_mw[i], rr.q_hv_mvar[i], rr.p_lv_mw[i], rr.q_lv_mvar[i]]
            load_pp = trafo_loading(net, i)
            imax = None
        mine = [r["pf"][k], r["qf"][k], r["pt"][k], r["qt"][k]]
        d_flow = max(d_flow, max(abs(a - c) for a, c in zip(pp_vals, mine)))
        if b["name"] == "grid":
            continue
        # loading recomputed from the independent flows: S / (sqrt(3) V) against the rating, worst end
        vf, vt = r["vm"][names.index(b["f"])] * buses[b["f"]], r["vm"][names.index(b["t"])] * buses[b["t"]]
        sf, st = math.hypot(mine[0], mine[1]), math.hypot(mine[2], mine[3])
        if b["kind"] == "line":
            ii = max(sf / (math.sqrt(3) * vf), st / (math.sqrt(3) * vt)) / imax * 100
        else:
            ii = max(sf, st) / b["sn"] * 100
        d_load = max(d_load, abs(ii - load_pp))
    # energy balance: generation minus power into the grid equals branch loss
    pcc = net.line.index[net.line.name == "grid"][0]
    loss = float(net.res_line.pl_mw.sum() - net.res_line.pl_mw[pcc] + net.res_trafo.pl_mw.sum())
    bal = abs(float(net.sgen.p_mw.sum()) - float(net.res_line.p_to_mw[pcc]) - loss)
    # the independent solver's own balance: slack output equals minus the net negative load plus its losses
    loss_ind = float(np.sum(r["pf"][1:] + r["pt"][1:]))  # all branches except the grid impedance (branch 0)
    return {"d_vm": d_vm, "d_va": d_va, "d_flow": d_flow, "d_load": d_load, "bal": bal, "loss_pp": loss, "loss_ind": loss_ind}


def open_line_q(v_kv=220.0):
    """Hand formula: reactive power into one export circuit left open at the far end, energised at v_kv.
    Pi circuit, Y_in = jB/2 + 1/(Z + 1/(jB/2)) with Z = (R + jX) L and B = 2 pi f C L; no pandapower."""
    L = P.LEN_EXP
    z = complex(P.EXP_R, P.EXP_X) * L
    b = 2 * math.pi * P.F_HZ * P.EXP_C * 1e-9 * L
    y_in = 1j * b / 2 + 1 / (z + 1 / (1j * b / 2))
    s = v_kv ** 2 * y_in.conjugate()  # MVA, S = V^2 conj(Y)
    return s.imag, v_kv ** 2 * b


def hand_vs_model():
    """Two hand checks. (1) open-ended circuit reactive power vs a pandapower run of the same circuit alone.
    (2) first array section current from the solved voltage vs the model's loading."""
    import pandapower as pp
    net = pp.create_empty_network(f_hz=P.F_HZ, sn_mva=P.BASE_MVA)
    a = pp.create_bus(net, vn_kv=220.0)
    z = pp.create_bus(net, vn_kv=220.0)
    pp.create_ext_grid(net, a, vm_pu=1.0)
    pp.create_line_from_parameters(net, a, z, length_km=P.LEN_EXP, r_ohm_per_km=P.EXP_R, x_ohm_per_km=P.EXP_X, c_nf_per_km=P.EXP_C, max_i_ka=1.0)
    pp.runpp(net, algorithm="nr", init="flat", tolerance_mva=1e-9, calculate_voltage_angles=True)
    q_model = float(net.res_line.q_from_mvar[0])
    q_hand, q_simple = open_line_q()
    res = json.loads((HERE.parent / "results" / "cases.json").read_text())["cases"]
    p_sec = P.N_TURB * P.P_TURB
    v1 = res["C1"]["bus_vm"]["S1T1"] * 66.0
    i_hand = p_sec / (math.sqrt(3) * v1) / P.ARR_IMAX_KA * 100  # MW / (sqrt3 kV) = kA; over the rating in kA; percent
    return {"q_open_hand": q_hand, "q_open_model": q_model, "q_open_simple_v2wc": q_simple,
            "dev_q_pct": abs(q_hand - q_model) / abs(q_model) * 100,
            "i_sec_hand_pct": i_hand, "i_sec_model_pct": res["C1"]["loadings"]["A1_1"], "v_s1t1_kv": v1}


def main():
    out = {"independent": {}}
    lines = []
    for case in CRIT["cases"]:
        d = independent(case)
        out["independent"][case["id"]] = d
        ok = d["d_vm"] <= TOL["X-VM"] and d["d_va"] <= TOL["X-VA"] and d["d_flow"] <= TOL["X-FLOW"] and d["d_load"] <= TOL["X-LOAD"] and d["bal"] <= TOL["BAL"]
        lines.append(f"{case['id']}: X-VM {d['d_vm']:.2e} pu (tol {TOL['X-VM']}), X-VA {d['d_va']:.2e} deg (tol {TOL['X-VA']}), X-FLOW {d['d_flow']:.2e} (tol {TOL['X-FLOW']}), "
                     f"X-LOAD {d['d_load']:.2e} pct (tol {TOL['X-LOAD']}), BAL {d['bal']:.2e} MW (tol {TOL['BAL']}), loss pandapower {d['loss_pp']:.4f} MW vs independent {d['loss_ind']:.4f} MW -> {'PASS' if ok else 'FAIL'}")
    h = hand_vs_model()
    out["hand"] = h
    h["dev_i_pct"] = abs(h["i_sec_hand_pct"] - h["i_sec_model_pct"]) / h["i_sec_model_pct"] * 100
    lines.append(f"HAND-1 open-ended 60 km circuit at 1.0 pu: Y_in formula gives {h['q_open_hand']:.3f} MVAr; pandapower on the same circuit alone gives {h['q_open_model']:.3f} MVAr; difference {h['dev_q_pct']:.4f} percent (tolerance {TOL['HAND']} percent). The simple V^2*omega*C*L figure is {h['q_open_simple_v2wc']:.2f} MVAr per circuit; two circuits {2*h['q_open_simple_v2wc']:.2f} MVAr.")
    lines.append(f"HAND-2 first array section in C1: 80 MW / (sqrt3 x {h['v_s1t1_kv']:.3f} kV) / 800 A = {h['i_sec_hand_pct']:.2f} percent; model loading {h['i_sec_model_pct']:.2f} percent; difference {h['dev_i_pct']:.3f} percent (tolerance {TOL['HAND']} percent; the hand figure ignores array charging and the loss between sections).")
    # first-order cause of the voltage rise: dV = Q x X in per unit on 100 MVA (hand estimate, no load flow)
    xg = (400.0 ** 2 / P.SCL_MVA) * P.GRID_XR / math.hypot(1, P.GRID_XR) / (400.0 ** 2 / P.BASE_MVA)
    xt = P.UK_ON / 100 * P.BASE_MVA / P.S_TR_ON / P.N_TR_ON
    res = json.loads((HERE.parent / "results" / "cases.json").read_text())["cases"]
    for cid in ("C1", "C4"):
        q = res[cid]["q_pcc_to_grid_mvar"] / P.BASE_MVA
        lines.append(f"EXPLAIN {cid}: reactive export at PCC {res[cid]['q_pcc_to_grid_mvar']:.1f} MVAr = {q:.3f} pu. Grid reactance {xg:.5f} pu gives rise {q*xg:.4f} pu at the PCC (model: {res[cid]['bus_vm']['PCC']:.4f} pu with remote bus at {CRIT['cases'][int(cid[1])-1]['grid_v_pu']} pu). "
                     f"Two onshore transformers in parallel have reactance {xt:.4f} pu and give a first-order rise {q*xt:.4f} pu from PCC to the 220 kV bus (model: {res[cid]['bus_vm']['ON220']-res[cid]['bus_vm']['PCC']:.4f} pu).")
    (HERE.parent / "results" / "checks.txt").write_text("\n".join(lines) + "\n")
    (HERE.parent / "results" / "checks.json").write_text(json.dumps(out, indent=1))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
