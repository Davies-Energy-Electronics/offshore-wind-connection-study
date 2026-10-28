"""LV13 base design, revision C: revision B (310 MVAr reactor in every case) with the cables LV14 sized,
re-sized on soil 1.5 K m/W (decision D1). Imports the LV13 builder and LV14 cable model unchanged."""
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEL = HERE.parents[2]
sys.path.insert(0, str(DEL / "LV13" / "connection-study" / "model"))
sys.path.insert(0, str(DEL / "LV13" / "connection-study" / "independent"))
sys.path.insert(0, str(DEL / "LV14" / "connection-study" / "model"))
import build as B  # noqa: E402
import params as P  # noqa: E402
from cable import Inputs, rating_a, smallest  # noqa: E402

import os
REV = os.environ.get("LV15_REV", "C")          # "C" (the step) or "D" (the final base design)
CRIT = json.load(open(HERE / ("criteria_D.json" if REV == "D" else "criteria_C.json")))
CASES = json.load(open(DEL / "LV13" / "connection-study" / "model" / "criteria.json"))["cases"]
LV14_DESIGN = json.load(open(DEL / "LV14" / "connection-study" / "results" / "design_currents.json"))
REACTOR_MVAR = 310.0
SOIL = 1.5
ARR = Inputs(un_kv=66.0, t_ins_mm=10.0, rho_soil=SOIL)
EXP = Inputs(un_kv=220.0, t_ins_mm=24.0, rho_soil=SOIL)


def sized():
    """Smallest series sizes meeting LV14's revision B design currents at soil 1.5 K m/W."""
    out = {}
    for key, x, i_des in (("array", ARR, LV14_DESIGN["array_first"]), ("export", EXP, LV14_DESIGN["export"])):
        a, i, p = smallest(x, i_des)
        out[key] = dict(area_mm2=a, rating_a=i, design_a=i_des, margin_pct=100 * (i / i_des - 1), r_ohm_km=p["R_ohm_km"], c_nf_km=p["c_nf_per_km"])
    return out


SIZED = sized()
if REV == "D":                                  # D5: the array re-sized on the revision C design current (W3)
    _a, _i, _p = smallest(ARR, 796.0)          # 796.0 A: revision C, C3, first array sections (results/n1.json)
    SIZED["array"] = dict(area_mm2=_a, rating_a=_i, design_a=796.0, margin_pct=100 * (_i / 796.0 - 1), r_ohm_km=_p["R_ohm_km"], c_nf_km=_p["c_nf_per_km"])


def apply_revc():
    """Point the LV13 parameters at the revision C cables (resistance at 90 C, capacitance, rating). Reactance unchanged."""
    P.EXP_R, P.EXP_C, P.EXP_IMAX_KA = SIZED["export"]["r_ohm_km"], SIZED["export"]["c_nf_km"], SIZED["export"]["rating_a"] / 1000
    P.ARR_R, P.ARR_C, P.ARR_IMAX_KA = SIZED["array"]["r_ohm_km"], SIZED["array"]["c_nf_km"], SIZED["array"]["rating_a"] / 1000


apply_revc()


def build(case, outage=None, scale=1.0, reactor=REACTOR_MVAR):
    """Revision C network for a case; outage is one of O1 to O5 (criteria_C.json); scale multiplies every turbine's P and Q."""
    if REV == "D" and outage == "O5":
        rx = reactor / 2                        # D6: two 155 MVAr units, one out
    else:
        rx = 0.0 if outage == "O5" else reactor
    net = B.build_pp(case, exp_c=P.EXP_C, reactor=rx if rx else None)
    if outage == "O5" and REV != "D" and len(net.shunt):
        net.shunt.drop(net.shunt.index, inplace=True)
    if outage == "O1":
        net.line.loc[net.line.name == "EXP1", "in_service"] = False
    elif outage == "O2":
        net.trafo.loc[net.trafo.name == "T_OSS1", "in_service"] = False
    elif outage == "O3":
        net.trafo.loc[net.trafo.name == "T_ON1", "in_service"] = False
    elif outage == "O4":
        net.line.loc[net.line.name == "A1_1", "in_service"] = False
        net.sgen.loc[net.sgen.name.str.startswith("S1T"), "in_service"] = False
    net.sgen["p_mw"] *= scale
    net.sgen["q_mvar"] *= scale
    return net
