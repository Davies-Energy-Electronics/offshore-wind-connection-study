"""(1) Sensitivity of the pandapower result to its two least certain set-up choices; (2) a hand-checkable number.

Least certain set-up choices (not data): the placeholder base voltage for case14 (the file has none) and the
solver initialisation and tolerance. Neither should move a per-unit result.

Hand check: on the 9-bus case the branch 8-2 is a lossless transformer (r = 0, x = 0.0625 pu), so its active
flow is P = V8 * V2 * sin(theta2 - theta8) / x, which a calculator reproduces from the bus voltages alone.

    python3 validation/sensitivity_and_hand_check.py
"""
import sys
from pathlib import Path

import numpy as np
import pandapower as pp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mpc  # noqa: E402
import run_validation as rv  # noqa: E402

ROOT = HERE.parent


def solve(case, kv=None, **over):
    old = rv.PLACEHOLDER_KV
    if kv:
        rv.PLACEHOLDER_KV = kv
    try:
        net = rv.build_net(case)
        kw = dict(rv.RUN_KW)
        kw.update(over)
        old_kw = rv.RUN_KW
        rv.RUN_KW = kw
        try:
            return rv.pandapower_results(net, case)
        finally:
            rv.RUN_KW = old_kw
    finally:
        rv.PLACEHOLDER_KV = old


def main():
    out = []
    c14 = mpc.read_case(ROOT / "casefiles" / "case14.m")
    base = solve(c14)
    for label, kw in (("placeholder 33 kV", dict(kv=33.0)), ("placeholder 345 kV", dict(kv=345.0)),
                      ("init=dc", dict(init="dc")), ("tolerance_mva=1e-6", dict(tolerance_mva=1e-6))):
        r = solve(c14, **kw)
        out.append(f"case14 {label:22s} max|dVm| {np.max(np.abs(r['vm'] - base['vm'])):.2e} pu  "
                   f"max|dVa| {np.max(np.abs(r['va_deg'] - base['va_deg'])):.2e} deg")
    c9 = mpc.read_case(ROOT / "casefiles" / "case9.m")
    r9 = solve(c9)
    pos = {int(n): i for i, n in enumerate(r9["bus_numbers"])}
    v8, v2 = r9["vm"][pos[8]], r9["vm"][pos[2]]
    th = np.deg2rad(r9["va_deg"][pos[2]] - r9["va_deg"][pos[8]])
    p_hand = v8 * v2 * np.sin(th) / 0.0625 * c9["baseMVA"]
    k = [i for i, (a, b) in enumerate(zip(c9["branch"][:, mpc.F_BUS], c9["branch"][:, mpc.T_BUS])) if (a, b) == (8, 2)][0]
    out.append(f"hand check, 9-bus branch 8-2: V8 {v8:.6f} pu, V2 {v2:.6f} pu, theta2-theta8 {np.rad2deg(th):.4f} deg")
    out.append(f"  P = V8*V2*sin(theta2-theta8)/x*100 = {p_hand:.4f} MW; pandapower flow leaving bus 2 into the branch {r9['pt'][k]:.4f} MW; "
               f"generator 2 output in the case file 163 MW")
    text = "\n".join(out)
    print(text)
    (ROOT / "results" / "sensitivity_and_hand_check.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
