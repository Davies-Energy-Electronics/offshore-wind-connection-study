# LV15: N-1, single-line diagram and report (revision C)

Builds on LV13 (model) and LV14 (cables, faults, grading) in the folders beside this one.

    ./run_all.sh           # n1.py, checks.py, sld.py, then the tests
    python3 model/report.py   # the report, from the saved results

- `model/criteria_C.json` the decisions D1 to D4 and the rules, committed before any run
- `model/revc.py` revision C: revision B plus the cables re-sized on soil 1.5 K m/W
- `model/n1.py` intact cases and five single outages, with curtailment by bisection
- `model/checks.py` the checks in the criteria and the labelled what-ifs W3 and W4
- `model/sld.py` the single-line diagram; `results/sld.png`
- `results/LV15_connection_study_report.pdf` the report covering LV12 to LV15

Self-directed study on ASSUMED data. No standard, grid code or SQSS was read; nothing claims compliance.
