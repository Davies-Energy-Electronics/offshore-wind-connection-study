"""LV15 tests: run after run_all.sh. Each checks a saved result against the model or a hand value."""
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "model"))
import revc  # noqa: E402
from cable import rating_a  # noqa: E402

R = HERE / "results"
N1 = json.load(open(R / "n1.json"))
CK = json.load(open(R / "checks.json"))


def test_revc_sizes_meet_revb_design_on_soil_1_5():
    for k in ("array", "export"):
        s = revc.SIZED[k]
        assert s["rating_a"] >= s["design_a"]
        # one size smaller must fail, so the choice is the smallest
        series = [95, 120, 150, 185, 240, 300, 400, 500, 630, 800, 1000, 1200, 1400, 1600, 2000]
        smaller = series[series.index(s["area_mm2"]) - 1]
        x = revc.ARR if k == "array" else revc.EXP
        assert rating_a(replace(x, area_mm2=smaller))[0] < s["design_a"]


def test_every_outage_and_case_reported():
    for o in ("O1", "O2", "O3", "O4", "O5"):
        assert set(N1["n1"][o]["cases"]) == {"C1", "C2", "C3", "C4"}
        for v in N1["n1"][o]["cases"].values():
            assert v["verdict"]


def test_energy_balance():
    assert CK["BAL"]["result"] == "PASS"


def test_string_outage_rides_through_everywhere():
    assert all(v["verdict"] == "RIDES THROUGH" for v in N1["n1"]["O4"]["cases"].values())


def test_transformer_outage_curtailment_by_hand():
    # one 250 MVA OSS transformer left at unity power factor: about 250 MW
    mw = N1["n1"]["O2"]["cases"]["C1"]["curtailed_mw"]
    assert abs(mw / 250.0 - 1) < 0.05


def test_export_outage_overloads_remaining_circuit():
    v = N1["n1"]["O1"]["cases"]["C1"]
    assert v["export_a"] > revc.SIZED["export"]["rating_a"]
    assert v["verdict"] == "CURTAILED"


def test_fault_levels_hardly_move_on_revc():
    assert CK["FAULT-C"]["worst_change_pct"] < 2.0


def test_charging_current_by_hand():
    # one export circuit's charging at 220 kV, from the revision C capacitance
    c = revc.SIZED["export"]["c_nf_km"] * 1e-9 * 60.0
    q = 220.0 ** 2 * 2 * math.pi * 50 * c
    assert 125 < q < 138      # MVAr: 220^2 x 314.16 x 144.08e-9 x 60 = 131.4 MVAr per circuit


# ---- revision D, the final base design
N1D = json.load(open(R / "n1_D.json"))
CKD = json.load(open(R / "checks_D.json"))


def test_revd_intact_all_inside_limits():
    assert all(not v["exceptions"] for v in N1D["intact"].values())


def test_revd_array_is_1000_and_rates_above_revc_current():
    a = N1D["sized"]["array"]
    assert a["area_mm2"] == 1000 and a["rating_a"] >= 796.0


def test_revd_one_reactor_unit_out_rides_through_at_full_output():
    for c in ("C1", "C2", "C3"):
        assert N1D["n1"]["O5"]["cases"][c]["verdict"] == "RIDES THROUGH"


def test_revd_r1_pickup_rule_and_margin():
    r = CKD["R1"]
    assert r["min_pickup_a"] <= 960.0 <= r["max_pickup_a"] and r["margin_s"] >= 0.30


def test_revd_fault_levels_hardly_move():
    assert CKD["FAULT-D"]["worst_change_pct"] < 2.0
