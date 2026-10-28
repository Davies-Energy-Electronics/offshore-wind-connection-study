"""Write results/tolerance_table.md from results/validation_results.json and criteria.json, and, with
--readme, replace the block between the TABLE markers in README.md.

    python3 validation/make_table.py --readme
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
crit = {c["id"]: c for c in json.loads((ROOT / "validation" / "criteria.json").read_text())["checks"]}
res = json.loads((ROOT / "results" / "validation_results.json").read_text())["checks"]


def fmt(x):
    return "-" if x is None else f"{x:.3g}"


rows = ["| Check | Case | Compared against | Quantity | Tolerance | Worst deviation | Unit | Verdict |", "|---|---|---|---|---|---|---|---|"]
for x in res:
    c = crit["C9-PUB" if x["check"].startswith("C9-PUB-") else x["check"]]
    tol = x["tolerance"] if x["tolerance"] is not None else (f"{c.get('tolerance_vm')} pu, {c.get('tolerance_va')} deg" if "tolerance_vm" in c else None)
    rows.append(f"| {x['check']} | {x['case']} | {c['against']} | {x["quantity"] or c.get("quantity", "")} | {fmt(tol) if not isinstance(tol, str) else tol} | "
                f"{fmt(x['max_abs_deviation'])} | {x['unit'] or '-'} | {x['verdict']} |")
table = "\n".join(rows)
(ROOT / "results" / "tolerance_table.md").write_text(table + "\n")
if "--readme" in sys.argv:
    p = ROOT / "README.md"
    s = p.read_text()
    a, b = s.index("<!-- TABLE -->") + len("<!-- TABLE -->"), s.index("<!-- /TABLE -->")
    p.write_text(s[:a] + "\n" + table + "\n" + s[b:])
print(table)
