"""Why does the printed IEEE 14-bus solution differ from the converged solution of its own data?

Solves the case with the independent solver, as published and with three deliberate changes to the data, and
prints the deviation from the printed solution for each. This is a diagnosis for the README, not a tuning
step: no tolerance in criteria.json was changed because of it.

    python3 validation/diagnose_14bus.py
"""
import copy
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import independent_nr as ind  # noqa: E402
import mpc  # noqa: E402


def report(case, ref, label):
    r = ind.solve(case)
    pos = {int(n): i for i, n in enumerate(case["bus"][:, mpc.BUS_I])}
    gq = np.array([r["gen_q"][pos[int(g)]] for g in ref["gen"][:, mpc.GEN_BUS]])
    return (f"{label:26s} max|dVm| {np.max(np.abs(r['vm'] - ref['bus'][:, mpc.VM])):.4f} pu  "
            f"max|dVa| {np.max(np.abs(r['va_deg'] - ref['bus'][:, mpc.VA])):.3f} deg  "
            f"max|dQg| {np.max(np.abs(gq - ref['gen'][:, mpc.QG])):.3f} MVAr  loss {r['loss_mw']:.3f} MW")


def main():
    ref = mpc.read_case(HERE.parent / "casefiles" / "case14.m")
    lines = [report(ref, ref, "data as published")]
    v = copy.deepcopy(ref)
    v["bus"][:, mpc.BS] = 0
    lines.append(report(v, ref, "bus 9 shunt removed"))
    v = copy.deepcopy(ref)
    t = v["branch"][:, mpc.TAP]
    v["branch"][:, mpc.TAP] = np.where(t == 0, 0, 1 / np.where(t == 0, 1, t))
    lines.append(report(v, ref, "tap ratios inverted"))
    v = copy.deepcopy(ref)
    v["branch"][:, mpc.BR_B] = 0
    lines.append(report(v, ref, "line charging removed"))
    text = "\n".join(lines)
    print(text)
    (HERE.parent / "results" / "diagnose_14bus.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
