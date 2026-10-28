"""Read the numeric tables of a MATPOWER case file (version 2 format): baseMVA, bus, gen and branch."""
import re
from pathlib import Path

import numpy as np

# MATPOWER column positions (zero based), from the case-format table in the MATPOWER manual
BUS_I, BUS_TYPE, PD, QD, GS, BS, VM, VA, BASE_KV = 0, 1, 2, 3, 4, 5, 7, 8, 9
GEN_BUS, PG, QG, VG, GEN_STATUS = 0, 1, 2, 5, 7
F_BUS, T_BUS, BR_R, BR_X, BR_B, TAP, SHIFT, BR_STATUS = 0, 1, 2, 3, 4, 8, 9, 10
REF, PV, PQ = 3, 2, 1


def _table(text, name):
    m = re.search(r"mpc\." + name + r"\s*=\s*\[(.*?)\];", text, re.S)
    if not m:
        raise ValueError(f"table mpc.{name} not found")
    rows = []
    for line in m.group(1).splitlines():
        line = line.split("%")[0].strip().rstrip(";").strip()
        if line:
            rows.append([float(x) for x in line.split()])
    return np.array(rows)


def read_case(path):
    text = Path(path).read_text()
    base = float(re.search(r"mpc\.baseMVA\s*=\s*([\d.]+)", text).group(1))
    return {"baseMVA": base, "bus": _table(text, "bus"), "gen": _table(text, "gen"), "branch": _table(text, "branch")}
