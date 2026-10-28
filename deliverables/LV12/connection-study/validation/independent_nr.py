"""A second, independent load-flow solver: polar Newton-Raphson in numpy, written from the textbook
equations and sharing no code with pandapower. It uses the MATPOWER branch model (pi circuit, tap on
the from side, phase shift), which is the data format of both published cases.

Used only to check pandapower: it reads the same case tables (validation/mpc.py) and nothing else.
"""
import numpy as np

from mpc import BR_B, BR_R, BR_STATUS, BR_X, BS, BUS_I, BUS_TYPE, F_BUS, GEN_BUS, GEN_STATUS, GS, PD, PG, PQ, PV, QD, QG, REF, SHIFT, T_BUS, TAP, VG


def solve(case, tol=1e-10, max_iter=30):
    base = case["baseMVA"]
    bus, gen, br = case["bus"], case["gen"], case["branch"]
    br = br[br[:, BR_STATUS] > 0]
    n = len(bus)
    idx = {int(b): i for i, b in enumerate(bus[:, BUS_I])}
    f = np.array([idx[int(x)] for x in br[:, F_BUS]])
    t = np.array([idx[int(x)] for x in br[:, T_BUS]])

    ys = 1.0 / (br[:, BR_R] + 1j * br[:, BR_X])
    bc = br[:, BR_B]
    tap = np.where(br[:, TAP] == 0, 1.0, br[:, TAP]) * np.exp(1j * np.deg2rad(br[:, SHIFT]))
    ytt = ys + 1j * bc / 2
    yff = ytt / (tap * np.conj(tap))
    yft = -ys / np.conj(tap)
    ytf = -ys / tap
    ysh = (bus[:, GS] + 1j * bus[:, BS]) / base

    nl = len(br)
    ybus = np.zeros((n, n), complex)
    for k in range(nl):
        ybus[f[k], f[k]] += yff[k]
        ybus[f[k], t[k]] += yft[k]
        ybus[t[k], f[k]] += ytf[k]
        ybus[t[k], t[k]] += ytt[k]
    ybus += np.diag(ysh)

    pg = np.zeros(n)
    vset = np.zeros(n)
    types = bus[:, BUS_TYPE].astype(int).copy()
    for g in gen[gen[:, GEN_STATUS] > 0]:
        i = idx[int(g[GEN_BUS])]
        pg[i] += g[PG]
        vset[i] = g[VG]
    p_spec = (pg - bus[:, PD]) / base
    q_spec = (-bus[:, QD]) / base  # used at PQ buses only

    vm = np.ones(n)
    va = np.zeros(n)
    for i in range(n):
        if types[i] in (PV, REF):
            vm[i] = vset[i]
    pv = np.where(types == PV)[0]
    pq = np.where(types == PQ)[0]
    ref = np.where(types == REF)[0]
    pvpq = np.r_[pv, pq]

    def injections(vm, va):
        v = vm * np.exp(1j * va)
        return v, v * np.conj(ybus @ v)

    for it in range(max_iter):
        v, s = injections(vm, va)
        mis = np.r_[(s.real - p_spec)[pvpq], (s.imag - q_spec)[pq]]
        if np.max(np.abs(mis)) < tol:
            break
        ibus = ybus @ v
        dS_dVa = 1j * np.diag(v) @ np.conj(np.diag(ibus) - ybus @ np.diag(v))
        dS_dVm = np.diag(v) @ np.conj(ybus @ np.diag(v / np.abs(v))) + np.conj(np.diag(ibus)) @ np.diag(v / np.abs(v))
        J = np.block([[dS_dVa.real[np.ix_(pvpq, pvpq)], dS_dVm.real[np.ix_(pvpq, pq)]],
                      [dS_dVa.imag[np.ix_(pq, pvpq)], dS_dVm.imag[np.ix_(pq, pq)]]])
        dx = np.linalg.solve(J, -mis)
        va[pvpq] += dx[:len(pvpq)]
        vm[pq] += dx[len(pvpq):]
    else:
        raise RuntimeError("independent Newton-Raphson did not converge")

    v, s = injections(vm, va)
    sf = v[f] * np.conj(yff * v[f] + yft * v[t]) * base
    st = v[t] * np.conj(ytf * v[f] + ytt * v[t]) * base
    gen_p = s.real * base + bus[:, PD]
    gen_q = s.imag * base + bus[:, QD]
    return {
        "iterations": it, "vm": vm, "va_deg": np.rad2deg(va - va[ref[0]]),
        "pf": sf.real, "qf": sf.imag, "pt": st.real, "qt": st.imag,
        "gen_p": gen_p, "gen_q": gen_q, "bus_numbers": bus[:, BUS_I].astype(int),
        "from": br[:, F_BUS].astype(int), "to": br[:, T_BUS].astype(int),
        "loss_mw": float(np.sum(sf.real + st.real)),
    }
