"""Fault levels at each busbar of the revision B base design.
Method: IEC 60909 voltage-source method as implemented in pandapower 3.5.6 (source code read, standard NOT read),
checked against an independent impedance-matrix calculation written here (numpy only).
Network data are the LV13 neutral table (build.network); shunt admittances are ignored, as the method does."""
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandapower as pp
import pandapower.shortcircuit as sc

import revb  # noqa: F401  (puts LV13 model on the path)
import build as B
import params as P

warnings.filterwarnings("ignore")
R = Path(__file__).resolve().parents[1] / "results"
BUSES = ["PCC", "ON220", "OSS220", "OSS66", "S1T8"]
CMAX, CMIN = 1.10, 1.00            # above 1 kV (values as coded in pandapower)
SCL_MAX, SCL_MIN = P.SCL_MVA, 5000.0
RX = 1.0 / P.GRID_XR               # R/X of the grid
K_WIND = 1.1                       # ASSUMED converter fault current, per unit of rated current. NOT SOURCED.


def sc_net(scl, wind, exp=None, arr=None):
    """exp / arr override (r, x, c_nf) of the export / array cable for a what-if."""
    buses, br = B.network()
    net = pp.create_empty_network(f_hz=P.F_HZ, sn_mva=P.BASE_MVA)
    ix = {n: pp.create_bus(net, vn_kv=kv, name=n) for n, kv in buses.items() if n != "REM"}
    pp.create_ext_grid(net, ix["PCC"], s_sc_max_mva=SCL_MAX, s_sc_min_mva=scl, rx_max=RX, rx_min=RX)
    for b in br:
        if b["name"] == "grid":
            continue
        if b["kind"] == "line":
            r, x, c = b["r"], b["x"], b["c_nf"]
            if exp and b["name"].startswith("EXP"):
                r, x, c = exp
            if arr and b["name"].startswith("A"):
                r, x, c = arr
            pp.create_line_from_parameters(net, ix[b["f"]], ix[b["t"]], length_km=b["km"], r_ohm_per_km=r, x_ohm_per_km=x,
                                           c_nf_per_km=c, max_i_ka=b["imax_ka"], name=b["name"])
        else:
            pp.create_transformer_from_parameters(net, ix[b["f"]], ix[b["t"]], sn_mva=b["sn"], vn_hv_kv=b["kv_hv"], vn_lv_kv=b["kv_lv"],
                                                  vk_percent=b["uk"], vkr_percent=b["ur"], pfe_kw=0.0, i0_percent=0.0, name=b["name"])
    net.line["endtemp_degree"] = 20.0   # no temperature correction: R as given in LV13 (pandapower needs the column in the min case)
    if wind:
        for n in buses:
            if n.startswith("S") and "T" in n:
                pp.create_sgen(net, ix[n], p_mw=0.0, sn_mva=P.P_TURB, k=K_WIND, current_source=True, name=n)
    return net, ix


def pp_faults(case, fault, scl, wind, **kw):
    net, ix = sc_net(scl, wind, **kw)
    sc.calc_sc(net, case=case, fault=fault, ip=(fault == "3ph"), ith=(fault == "3ph"), tk_s=1.0, branch_results=True)
    out = {}
    for n in BUSES:
        r = net.res_bus_sc.loc[ix[n]]
        out[n] = dict(ikss_ka=float(r.ikss_ka), ip_ka=float(r.ip_ka) if fault == "3ph" else None,
                      ith_ka=float(r.ith_ka) if fault == "3ph" else None,
                      skss_mva=float(r.skss_mw) if "skss_mw" in r.index else None)
    return out, net, ix


def ybus(case, scl, drop=()):
    c = CMAX if case == "max" else CMIN
    """Nodal admittance matrix (per unit on 100 MVA) of the grid-only short-circuit network, and its elements.
    Grid Z = c Un^2 / Sk'' (IEC 60909 form), c = cmax or cmin, so the grid impedance depends on the case.
    Transformers: K_T = 0.95 cmax / (1 + 0.6 xT) in the max case only; lines: series R + jX only (C ignored).
    `drop` is a set of branch names taken out of service (informational N-1 only)."""
    buses, br = B.network()
    names = [n for n in buses if n != "REM"]
    idx = {n: i for i, n in enumerate(names)}
    Y = np.zeros((len(names), len(names)), complex)
    sb = P.BASE_MVA
    elems = []

    def add(name, a, b, z):
        y = 1 / z
        Y[a, a] += y
        if b is not None:
            Y[b, b] += y
            Y[a, b] -= y
            Y[b, a] -= y
        elems.append((name, a, b, z))
    zg = c * (1.0 ** 2 / (scl / sb)) * complex(RX, 1) / abs(complex(RX, 1))
    add("grid", idx["PCC"], None, zg)
    for b in br:
        if b["name"] == "grid" or b["name"] in drop:
            continue
        if b["kind"] == "line":
            zb = buses[b["f"]] ** 2 / sb
            add(b["name"], idx[b["f"]], idx[b["t"]], complex(b["r"], b["x"]) * b["km"] / zb)
        else:
            zt = b["uk"] / 100 * sb / b["sn"]
            rt = b["ur"] / 100 * sb / b["sn"]
            xt = math.sqrt(zt ** 2 - rt ** 2)
            x_own = math.sqrt((b["uk"] / 100) ** 2 - (b["ur"] / 100) ** 2)   # on the transformer's own rating
            kt = 0.95 * CMAX / (1 + 0.6 * x_own) if case == "max" else 1.0
            add(b["name"], idx[b["f"]], idx[b["t"]], kt * complex(rt, xt))
    return Y, idx, elems, buses


def zbus_grid_only(case, scl):
    """Independent: Ik'' = c Un / (sqrt3 |Zk|) from the nodal admittance matrix."""
    c = CMAX if case == "max" else CMIN
    Y, idx, _, buses = ybus(case, scl)
    Z = np.linalg.inv(Y)
    return {n: c * P.BASE_MVA / (math.sqrt(3) * buses[n]) / abs(Z[idx[n], idx[n]]) for n in BUSES}


def branch_currents_ka(fault_bus, case, scl, three_phase=True, drop=()):
    """Grid-only fault current (kA) in every element for a bolted fault at fault_bus.
    Returned as {element: (current at its from-end in kA, at its to-end in kA)}; the grid source is keyed 'grid'."""
    c = CMAX if case == "max" else CMIN
    Y, idx, elems, buses = ybus(case, scl, drop)
    Z = np.linalg.inv(Y)
    k = idx[fault_bus]
    i_f = c / Z[k, k]                        # pu
    v = c - Z[:, k] * i_f                    # bus voltage pu during the fault
    out = {}
    names = list(buses)
    for nme, a, b, z in elems:
        va = v[a]
        vb = c if b is None else v[b]            # the grid element runs from the source (voltage c) to PCC
        i_pu = abs((va - vb) / z)
        if b is None:
            out[nme] = (i_pu * P.BASE_MVA / (math.sqrt(3) * buses["PCC"]), 0.0)
            continue
        fb = [n for n in buses if n != "REM"]
        kv_a, kv_b = buses[fb[a]], buses[fb[b]]
        out[nme] = (i_pu * P.BASE_MVA / (math.sqrt(3) * kv_a), i_pu * P.BASE_MVA / (math.sqrt(3) * kv_b))
    scale = 1.0 if three_phase else math.sqrt(3) / 2
    return {n: (a * scale, b * scale) for n, (a, b) in out.items()}


def run():
    out = {"method": "pandapower 3.5.6 calc_sc (IEC 60909 implementation) + independent Zbus", "cmax": CMAX, "cmin": CMIN,
           "scl_max_mva": SCL_MAX, "scl_min_mva": SCL_MIN, "k_wind": K_WIND}
    mx, _, _ = pp_faults("max", "3ph", SCL_MAX, True)
    mx_grid, _, _ = pp_faults("max", "3ph", SCL_MAX, False)
    mn3, _, _ = pp_faults("min", "3ph", SCL_MIN, False)
    mn2, _, _ = pp_faults("min", "2ph", SCL_MIN, False)
    ind_max = zbus_grid_only("max", SCL_MAX)
    ind_min = zbus_grid_only("min", SCL_MIN)
    rows = []
    worst = 0.0
    for n in BUSES:
        e1 = 100 * abs(mx_grid[n]["ikss_ka"] / ind_max[n] - 1)
        e2 = 100 * abs(mn3[n]["ikss_ka"] / ind_min[n] - 1)
        e3 = 100 * abs(mn2[n]["ikss_ka"] / (math.sqrt(3) / 2 * ind_min[n]) - 1)
        worst = float(max(worst, e1, e2, e3))
        rows.append(dict(bus=n, kv=B.network()[0][n], max3_total_ka=mx[n]["ikss_ka"], max3_grid_only_ka=mx_grid[n]["ikss_ka"],
                         ip_ka=mx[n]["ip_ka"], ith_ka_1s=mx[n]["ith_ka"], max_mva=math.sqrt(3) * B.network()[0][n] * mx[n]["ikss_ka"],
                         min3_ka=mn3[n]["ikss_ka"], min2_ka=mn2[n]["ikss_ka"],
                         indep_max_grid_only_ka=ind_max[n], indep_min3_ka=ind_min[n], err_pct=[float(e1), float(e2), float(e3)]))
    out["rows"] = rows
    out["worst_error_percent"] = worst
    # what-if W2: cable electrical data as sized (R from cable.py at 90 C, X and the length as LV13, C from the geometry)
    sz = json.load(open(R / "cable_sizing.json"))
    ep, ap = sz["export"]["parts"], sz["array"]["parts"]
    w2, _, _ = pp_faults("max", "3ph", SCL_MAX, True, exp=(ep["R_ohm_km"], P.EXP_X, ep["c_nf_per_km"]), arr=(ap["R_ohm_km"], P.ARR_X, ap["c_nf_per_km"]))
    out["w2_max3_total_ka"] = {n: w2[n]["ikss_ka"] for n in BUSES}
    json.dump(out, open(R / "faults.json", "w"), indent=1)
    return out


if __name__ == "__main__":
    o = run()
    print(f"{'bus':7}{'kV':>5}{'Ik3max tot':>11}{'grid only':>10}{'ip':>8}{'Ith1s':>8}{'MVA':>8}{'Ik3min':>8}{'Ik2min':>8}   indep(max,min)   err% ")
    for r in o["rows"]:
        print(f"{r['bus']:7}{r['kv']:5.0f}{r['max3_total_ka']:11.3f}{r['max3_grid_only_ka']:10.3f}{r['ip_ka']:8.3f}{r['ith_ka_1s']:8.3f}{r['max_mva']:8.0f}{r['min3_ka']:8.3f}{r['min2_ka']:8.3f}   {r['indep_max_grid_only_ka']:.3f} {r['indep_min3_ka']:.3f}   {[round(e,5) for e in r['err_pct']]}")
    print("worst error percent", o["worst_error_percent"])
    print("W2", o["w2_max3_total_ka"])
