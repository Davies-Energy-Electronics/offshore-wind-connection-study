"""One neutral description of the network; two builders (pandapower and a MATPOWER-style table for the
independent solver) read it, so the two solvers see the same data and share no solver code."""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "independent"))
import params as P  # noqa: E402

W = 2 * math.pi * P.F_HZ


def network(scl_mva=P.SCL_MVA, exp_c=P.EXP_C):
    """Return buses {name: kV} and branches [dict]. Bus names: REM (remote grid, slack), PCC (400 kV),
    ON220, OSS220, OSS66, S{i}T{j} (string i turbine j)."""
    buses = {"REM": 400.0, "PCC": 400.0, "ON220": 220.0, "OSS220": 220.0, "OSS66": 66.0}
    br = []
    zg = 400.0 ** 2 / scl_mva
    xg = zg * P.GRID_XR / math.hypot(1, P.GRID_XR)
    br.append(dict(name="grid", kind="line", f="REM", t="PCC", r=xg / P.GRID_XR, x=xg, c_nf=0.0, km=1.0, imax_ka=1e3))
    for k in range(P.N_TR_ON):
        br.append(dict(name=f"T_ON{k+1}", kind="trafo", f="PCC", t="ON220", sn=P.S_TR_ON, uk=P.UK_ON, ur=P.UR_ON, kv_hv=400.0, kv_lv=220.0))
    for k in range(P.N_EXP):
        br.append(dict(name=f"EXP{k+1}", kind="line", f="ON220", t="OSS220", r=P.EXP_R, x=P.EXP_X, c_nf=exp_c, km=P.LEN_EXP, imax_ka=P.EXP_IMAX_KA))
    for k in range(P.N_TR_OSS):
        br.append(dict(name=f"T_OSS{k+1}", kind="trafo", f="OSS220", t="OSS66", sn=P.S_TR_OSS, uk=P.UK_OSS, ur=P.UR_OSS, kv_hv=220.0, kv_lv=66.0))
    for i in range(1, P.N_STRINGS + 1):
        prev = "OSS66"
        for j in range(1, P.N_TURB + 1):
            b = f"S{i}T{j}"
            buses[b] = 66.0
            br.append(dict(name=f"A{i}_{j}", kind="line", f=prev, t=b, r=P.ARR_R, x=P.ARR_X, c_nf=P.ARR_C,
                           km=P.LEN_FIRST if j == 1 else P.LEN_STEP, imax_ka=P.ARR_IMAX_KA))
            prev = b
    return buses, br


def inject(case):
    """Turbine P, Q per turbine (MW, MVAr; generation positive) for a case dict from criteria.json."""
    p = case["p_mw"] / (P.N_STRINGS * P.N_TURB)
    t = math.tan(math.acos(P.ASSUMPTIONS["A18"][1]))
    q = {"unity": 0.0, "0.95 exporting Q": p * t, "0.95 absorbing Q": -p * t}[case["pf"]]
    return p, q


def reactor_for(case, exp_c, reactor):
    """MVAr of the onshore reactor: the base rule (A14) unless a what-if value is given."""
    if reactor is not None:
        return reactor
    return P.reactor_mvar(exp_c) if case["reactor"] else 0.0


def build_pp(case, scl_mva=P.SCL_MVA, exp_c=P.EXP_C, reactor=None):
    import pandapower as pp
    buses, br = network(scl_mva, exp_c)
    net = pp.create_empty_network(f_hz=P.F_HZ, sn_mva=P.BASE_MVA)
    ix = {n: pp.create_bus(net, vn_kv=kv, name=n) for n, kv in buses.items()}
    pp.create_ext_grid(net, ix["REM"], vm_pu=case["grid_v_pu"], va_degree=0.0)
    for b in br:
        if b["kind"] == "line":
            pp.create_line_from_parameters(net, ix[b["f"]], ix[b["t"]], length_km=b["km"], r_ohm_per_km=b["r"], x_ohm_per_km=b["x"],
                                           c_nf_per_km=b["c_nf"], max_i_ka=b["imax_ka"], name=b["name"])
        else:
            pp.create_transformer_from_parameters(net, ix[b["f"]], ix[b["t"]], sn_mva=b["sn"], vn_hv_kv=b["kv_hv"], vn_lv_kv=b["kv_lv"],
                                                  vk_percent=b["uk"], vkr_percent=b["ur"], pfe_kw=0.0, i0_percent=0.0, name=b["name"])
    p, q = inject(case)
    for n in buses:
        if n.startswith("S") and "T" in n:
            pp.create_sgen(net, ix[n], p_mw=p, q_mvar=q, name=n)
    qr = reactor_for(case, exp_c, reactor)
    if qr:
        pp.create_shunt(net, ix["ON220"], q_mvar=qr, p_mw=0.0, vn_kv=220.0, name="reactor")
    return net


def solve_pp(net):
    import pandapower as pp
    pp.runpp(net, algorithm="nr", init="flat", tolerance_mva=1e-9, max_iteration=50, calculate_voltage_angles=True, enforce_q_lims=False)
    return net


def build_mpc(case, scl_mva=P.SCL_MVA, exp_c=P.EXP_C, reactor=None):
    """MATPOWER-style tables on a 100 MVA base, written from the same neutral description."""
    import mpc as M
    buses, br = network(scl_mva, exp_c)
    names = list(buses)
    idx = {n: i + 1 for i, n in enumerate(names)}
    bus = np.zeros((len(names), 13))
    for n, i in idx.items():
        bus[i - 1, M.BUS_I] = i
        bus[i - 1, M.BUS_TYPE] = M.REF if n == "REM" else M.PQ
        bus[i - 1, M.VM] = 1.0
        bus[i - 1, M.BASE_KV] = buses[n]
    p, q = inject(case)
    for n in names:
        if n.startswith("S") and "T" in n:
            bus[idx[n] - 1, M.PD] = -p  # generation as negative load
            bus[idx[n] - 1, M.QD] = -q
    qr = reactor_for(case, exp_c, reactor)
    if qr:
        bus[idx["ON220"] - 1, M.BS] = -qr  # inductive shunt, MVAr at 1 pu
    gen = np.zeros((1, 10))
    gen[0, M.GEN_BUS] = idx["REM"]
    gen[0, M.VG] = case["grid_v_pu"]
    gen[0, M.GEN_STATUS] = 1
    rows = []
    for b in br:
        row = np.zeros(11)
        row[M.F_BUS], row[M.T_BUS], row[M.BR_STATUS] = idx[b["f"]], idx[b["t"]], 1
        if b["kind"] == "line":
            zb = buses[b["f"]] ** 2 / P.BASE_MVA
            row[M.BR_R], row[M.BR_X] = b["r"] * b["km"] / zb, b["x"] * b["km"] / zb
            row[M.BR_B] = W * b["c_nf"] * 1e-9 * b["km"] * zb
        else:
            zt = b["uk"] / 100 * P.BASE_MVA / b["sn"]
            rt = b["ur"] / 100 * P.BASE_MVA / b["sn"]
            row[M.BR_R], row[M.BR_X] = rt, math.sqrt(zt ** 2 - rt ** 2)
        rows.append(row)
    return {"baseMVA": P.BASE_MVA, "bus": bus, "gen": gen, "branch": np.array(rows)}, names, br, buses
