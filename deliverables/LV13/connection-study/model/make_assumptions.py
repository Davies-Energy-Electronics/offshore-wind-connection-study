"""Write results/assumptions.md from params.py (the only place the assumptions live)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import params as P  # noqa: E402

rows = ["| ID | Assumption | Value | Unit | Status | Note | Where |", "|---|---|---|---|---|---|---|"]
for k, (d, v, u, s, n) in P.ASSUMPTIONS.items():
    if v == "computed":
        v = f"{P.reactor_mvar():.0f}"
    elif v is None:
        v = "omitted"
    elif isinstance(v, tuple):
        v = ", ".join(str(x) for x in v)
    rows.append(f"| {k} | {d} | {v} | {u} | {s} | {n} | [calc: connection-study/model/params.py] |")
(HERE.parent / "results" / "assumptions.md").write_text("\n".join(rows) + "\n")
print("\n".join(rows))
