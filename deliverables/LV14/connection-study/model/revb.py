"""LV13 base design, revision B: the LV13 model with a 310 MVAr onshore reactor in every case (decision 7).
Imports the LV13 builder unchanged; only the reactor value is passed in."""
import json
import sys
from pathlib import Path

LV13 = Path(__file__).resolve().parents[3] / "LV13" / "connection-study"
sys.path.insert(0, str(LV13 / "model"))
sys.path.insert(0, str(LV13 / "independent"))
import build as B  # noqa: E402
import params as P  # noqa: E402
import pandapower as pp  # noqa: E402

REACTOR_MVAR = 310.0
CASES = json.load(open(LV13 / "model" / "criteria.json"))["cases"]


def solve_case(case):
    net = B.build_pp(case, reactor=REACTOR_MVAR)
    B.solve_pp(net)
    return net


def design_currents():
    """Largest line currents (A) over C1 to C4: array first section, any array section, export circuit."""
    out = {"array_first": 0.0, "array_any": 0.0, "export": 0.0, "cases": {}}
    for c in CASES:
        net = solve_case(c)
        i = net.res_line.i_ka * 1000
        name = net.line.name
        af = i[name.str.match(r"A\d+_1$")].max()
        aa = i[name.str.startswith("A")].max()
        ex = i[name.str.startswith("EXP")].max()
        out["cases"][c["id"]] = dict(array_first_A=af, export_A=ex, pcc_v=float(net.res_bus.vm_pu[net.bus.name == "PCC"].iloc[0]),
                                     max_v=float(net.res_bus.vm_pu.max()), min_v=float(net.res_bus.vm_pu.min()))
        out["array_first"] = max(out["array_first"], af)
        out["array_any"] = max(out["array_any"], aa)
        out["export"] = max(out["export"], ex)
    return out


if __name__ == "__main__":
    d = design_currents()
    json.dump(d, open(Path(__file__).resolve().parents[1] / "results" / "design_currents.json", "w"), indent=1)
    print(json.dumps(d, indent=1))
