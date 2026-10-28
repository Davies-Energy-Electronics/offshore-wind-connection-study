"""Sensitivity on the two least certain inputs (grid short-circuit level; export cable capacitance) and one
labelled what-if remedy. Writes results/sensitivity.txt and results/whatif.txt. Not part of the pass rule."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import params as P  # noqa: E402
from run_cases import CRIT, run_all  # noqa: E402


def summ(res):
    row = []
    for cid, r in res.items():
        v = r["voltage"]
        vmax = max(v["220 kV buses"]["max"], v["66 kV OSS"]["max"], v["66 kV array"]["max"])
        vmin = min(v["220 kV buses"]["min"], v["66 kV OSS"]["min"], v["66 kV array"]["min"])
        ld = r["loading_max"]
        row.append(f"{cid}: PCC {v['PCC 400 kV']['max']:.4f}, internal max {vmax:.4f} min {vmin:.4f}, cables {max(ld['array'], ld['export']):.1f}, trafo {max(ld['oss_trafo'], ld['onshore_trafo']):.1f} percent, exceptions {len(r['exceptions'])}")
    return row


def main():
    lines = ["SENSITIVITY (one input moved at a time; base = 10000 MVA, 170 nF/km)"]
    runs = {"base": {}, "SCL 5000 MVA": {"scl": 5000.0}, "SCL 20000 MVA": {"scl": 20000.0},
            "export C -20 percent (136 nF/km)": {"exp_c": P.EXP_C * 0.8}, "export C +20 percent (204 nF/km)": {"exp_c": P.EXP_C * 1.2}}
    base = run_all()
    for name, kw in runs.items():
        res = base if not kw else run_all(**kw)
        lines.append(f"-- {name}")
        lines += ["   " + s for s in summ(res)]
        if kw:
            flips = [cid for cid in res if bool(res[cid]["exceptions"]) != bool(base[cid]["exceptions"])]
            lines.append(f"   verdict flips against base: {flips if flips else 'none'}")
    (HERE.parent / "results" / "sensitivity.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

    q_total = round(P.N_EXP * 220.0 ** 2 * 2 * 3.141592653589793 * P.F_HZ * P.EXP_C * 1e-9 * P.LEN_EXP, -1)
    w = run_all(reactor=q_total)
    out = [f"WHAT-IF W1 (NOT part of the pass rule; chosen after the base results were seen): onshore 220 kV shunt reactor of {q_total:.0f} MVAr (about 100 percent of nominal total export cable charging) in service in ALL four cases"]
    out += ["   " + s for s in summ(w)]
    for cid, r in w.items():
        for e in r["exceptions"]:
            out.append(f"   {cid}: {e}")
        out.append(f"   {cid}: Q into grid {r['q_pcc_to_grid_mvar']:.1f} MVAr, P into grid {r['p_pcc_to_grid_mw']:.2f} MW")
    (HERE.parent / "results" / "whatif.txt").write_text("\n".join(out) + "\n")
    (HERE.parent / "results" / "whatif.json").write_text(json.dumps({"reactor_mvar": q_total, "cases": w}, indent=1))
    print("\n".join(out))


if __name__ == "__main__":
    main()
