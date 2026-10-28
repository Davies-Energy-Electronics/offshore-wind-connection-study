"""Run from connection-study/: python3 -m pytest -q"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))
import checks  # noqa: E402
import params as P  # noqa: E402
from run_cases import CRIT, run_all  # noqa: E402

RES = run_all()


def test_criteria_revision_a_has_four_cases():
    assert CRIT["revision"] == "A"
    assert [c["id"] for c in CRIT["cases"]] == ["C1", "C2", "C3", "C4"]


def test_installed_capacity_is_400_mw():
    assert P.N_STRINGS * P.N_TURB * P.P_TURB == 400.0


def test_all_cases_converge():
    assert all(r["converged"] for r in RES.values())


def test_independent_solver_agrees():
    for case in CRIT["cases"]:
        d = checks.independent(case)
        assert d["d_vm"] <= 1e-6 and d["d_va"] <= 1e-4 and d["d_flow"] <= 1e-4 and d["d_load"] <= 1e-3 and d["bal"] <= 1e-6


def test_recorded_exceptions_match_a_fresh_run():
    saved = json.loads((ROOT / "results" / "cases.json").read_text())["cases"]
    for cid, r in RES.items():
        assert r["exceptions"] == saved[cid]["exceptions"]


def test_hand_check_open_line_charging():
    q_hand, _ = checks.open_line_q()
    h = checks.hand_vs_model()
    assert abs(q_hand - h["q_open_model"]) / abs(h["q_open_model"]) * 100 <= 0.5
