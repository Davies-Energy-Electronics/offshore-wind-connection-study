"""Tests for the LV12 validation. They pin the recorded outcome of criteria revision A, including the
three checks that did not pass, so a change in pandapower or in the data shows up as a failing test.

    python3 casefiles/fetch_data.py && python3 -m pytest -q
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "validation"))
import independent_nr  # noqa: E402
import mpc  # noqa: E402
import run_validation as rv  # noqa: E402

CRITERIA = json.loads((ROOT / "validation" / "criteria.json").read_text())
CRITERIA_TOL = {c["id"]: c.get("tolerance") for c in CRITERIA["checks"]}


@pytest.fixture(scope="module")
def checks(tmp_path_factory):
    assert rv.main() in (0, 1)
    data = json.loads((ROOT / "results" / "validation_results.json").read_text())
    return {(x["check"], x["case"]): x for x in data["checks"]}


def test_criteria_revision_and_ids_are_present(checks):
    assert CRITERIA["revision"] == "A"
    ids = {c["id"] for c in CRITERIA["checks"]}
    # C9-PUB-VM and C9-PUB-VA are the two halves of criterion C9-PUB, run only when the table is supplied
    assert {("C9-PUB" if k[0].startswith("C9-PUB-") else k[0]) for k in checks} <= ids


@pytest.mark.parametrize("case", ["case9", "case14"])
@pytest.mark.parametrize("cid", ["X-VM", "X-VA", "X-FLOW", "X-LOSS"])
def test_pandapower_matches_the_independent_solver(checks, cid, case):
    assert checks[(cid, case)]["verdict"] == "PASS"


@pytest.mark.parametrize("cid", ["C14-PUB-VA", "C14-PUB-PG", "C14-PUB-LOSS"])
def test_case14_published_checks_that_pass(checks, cid):
    assert checks[(cid, "case14")]["verdict"] == "PASS"


FINDINGS = {f["id"]: f for f in json.loads((ROOT / "validation" / "findings.json").read_text())["findings"]}


def test_criteria_revision_a_tolerances_are_unchanged():
    tol = {c["id"]: c.get("tolerance") for c in CRITERIA["checks"]}
    assert CRITERIA["revision"] == "A"
    assert tol["C14-PUB-VM"] == 0.001 and tol["C14-PUB-VA"] == 0.05 and tol["C14-PUB-QG"] == 0.1
    assert tol["C14-PUB-PG"] == 0.1 and tol["C14-PUB-LOSS"] == 0.1


def test_f001_case14_voltage_miss_is_pinned(checks):
    # Fails if the deviation grows or shrinks, or if the verdict flips to PASS: a changed finding must be looked at.
    f, x = FINDINGS["F-001"], checks[("C14-PUB-VM", "case14")]
    assert f["status"] == "OPEN" and f["cause"] == "NOT SOURCED"
    assert x["verdict"] == "FAIL"
    assert x["max_abs_deviation"] == pytest.approx(f["pinned_deviation_pu"], abs=f["pin_tolerance_pu"])
    case = mpc.read_case(ROOT / "casefiles" / "case14.m")
    r = rv.pandapower_results(rv.build_net(case), case)
    dev = np.abs(r["vm"] - case["bus"][:, mpc.VM])
    assert int(r["bus_numbers"][int(np.argmax(dev))]) == f["worst_bus"]
    assert [int(b) for b in r["bus_numbers"][dev > CRITERIA_TOL["C14-PUB-VM"]]] == [f["worst_bus"]]


def test_f002_case14_reactive_miss_is_pinned(checks):
    f, x = FINDINGS["F-002"], checks[("C14-PUB-QG", "case14")]
    assert f["status"] == "OPEN" and f["cause"] == "NOT SOURCED"
    assert x["verdict"] == "FAIL"
    assert x["max_abs_deviation"] == pytest.approx(f["pinned_worst_deviation_mvar"], abs=f["pin_tolerance_mvar"])
    case = mpc.read_case(ROOT / "casefiles" / "case14.m")
    r = rv.pandapower_results(rv.build_net(case), case)
    pos = {int(n): i for i, n in enumerate(r["bus_numbers"])}
    for bus, value in f["computed_mvar"].items():
        assert r["gen_q"][pos[int(bus)]] == pytest.approx(value, abs=f["pin_tolerance_mvar"])
        assert f["published_mvar"][bus] == pytest.approx(case["gen"][case["gen"][:, mpc.GEN_BUS] == int(bus), mpc.QG][0])


def test_bundled_case14_equals_the_matpower_data(checks):
    assert checks[("D-BUNDLED", "case14")]["verdict"] == "PASS"


def test_bundled_case9_differs_from_the_matpower_data(checks):
    # pandapower's bundled case9 sets every generator voltage to 1.0 pu; the MATPOWER file sets 1.04, 1.025, 1.025
    x = checks[("D-BUNDLED", "case9")]
    assert x["verdict"] == "FAIL"
    assert "4.000e-02" in x["detail"]


def test_case9_published_table_is_reported_open_while_no_table_is_supplied(checks):
    if (ROOT.parent.parent.parent / "inputs" / "LV12" / "case9_published.csv").exists():
        pytest.skip("a published table was supplied")
    assert checks[("C9-PUB", "case9")]["verdict"] == "OPEN"


def test_case9_against_anderson_and_fouad_when_supplied(checks):
    if not (ROOT.parent.parent.parent / "inputs" / "LV12" / "case9_published.csv").exists():
        pytest.skip("no published table supplied")
    assert checks[("C9-PUB-VM", "case9")]["verdict"] == "PASS"
    assert checks[("C9-PUB-VA", "case9")]["verdict"] == "PASS"


def test_independent_solver_satisfies_its_own_mismatch_tolerance():
    for name in ("case9", "case14"):
        case = mpc.read_case(ROOT / "casefiles" / f"{name}.m")
        r = independent_nr.solve(case)
        assert r["iterations"] < 10


def test_independent_solver_energy_balance():
    case = mpc.read_case(ROOT / "casefiles" / "case14.m")
    r = independent_nr.solve(case)
    assert r["gen_p"].sum() - case["bus"][:, mpc.PD].sum() == pytest.approx(r["loss_mw"], abs=1e-6)
