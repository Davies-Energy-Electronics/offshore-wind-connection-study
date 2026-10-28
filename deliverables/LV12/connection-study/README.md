# Connection study: pandapower validation (LV12)

Block 1 of 4 of a self-directed grid-connection study for a 400 MW offshore wind farm. This block checks the
tool before anything is built on it: does pandapower reproduce the published IEEE 9-bus and 14-bus load flows?

**Honesty paragraph.** This is self-directed work on public test cases and assumed data. It is not professional
experience, it has not been reviewed by a chartered engineer, and no standard is cited here that has not been read.
Status of this block: prepared and checked by a second solver; **not yet approved** (approval is the author's own
reproduction of one number by hand, below). Licence: GPL-3.0 (`LICENSE`).

## Result in one table

Tolerances were written before the first run (`validation/criteria.json`, revision A, its own commit). The rule:
a published-comparison tolerance is twice the half-unit of the last printed digit of the published value; a
solver-to-solver tolerance is set by the convergence tolerance of both solvers. Worst deviation is the largest
absolute difference over all buses, generators or branches in the case. Verdict words: PASS and FAIL against the
tolerance; OPEN means the comparison could not be made; INFORMATIONAL means it is reported but is not a pass criterion.

<!-- TABLE -->
| Check | Case | Compared against | Quantity | Tolerance | Worst deviation | Unit | Verdict |
|---|---|---|---|---|---|---|---|
| X-VM | case9 | independent solver | bus voltage magnitude | 1e-06 | 4.44e-16 | pu | PASS |
| X-VA | case9 | independent solver | bus voltage angle | 0.0001 | 8.88e-15 | degree | PASS |
| X-FLOW | case9 | independent solver | branch active and reactive flow, both ends | 0.0001 | 6.24e-13 | MW or MVAr | PASS |
| X-LOSS | case9 | independent solver | total active loss | 0.0001 | 2.13e-14 | MW | PASS |
| D-BUNDLED | case9 | pandapower bundled case | bus voltage magnitude and angle after solving | 1e-06 pu, 0.0001 deg | 0.389 | degree | FAIL |
| C9-CHOW-QG | case9 | case file generator table (Chow 1982 via MATPOWER) | generator reactive output | 0.15 | 0.114 | MVAr | INFORMATIONAL |
| C9-CHOW-PG1 | case9 | case file generator table (Chow 1982 via MATPOWER) | slack active output | 0.1 | 0.659 | MW | INFORMATIONAL |
| C9-PUB-VM | case9 | published solution table | bus voltage magnitude | 0.001 | 0.000369 | pu | PASS |
| C9-PUB-VA | case9 | published solution table | bus voltage angle | 0.05 | 0.0352 | degree | PASS |
| X-VM | case14 | independent solver | bus voltage magnitude | 1e-06 | 4.44e-16 | pu | PASS |
| X-VA | case14 | independent solver | bus voltage angle | 0.0001 | 2.66e-14 | degree | PASS |
| X-FLOW | case14 | independent solver | branch active and reactive flow, both ends | 0.0001 | 8.42e-13 | MW or MVAr | PASS |
| X-LOSS | case14 | independent solver | total active loss | 0.0001 | 1.05e-13 | MW | PASS |
| D-BUNDLED | case14 | pandapower bundled case | bus voltage magnitude and angle after solving | 1e-06 pu, 0.0001 deg | 2.13e-14 | degree | PASS |
| C14-PUB-VM | case14 | published | bus voltage magnitude | 0.001 | 0.00133 | pu | FAIL |
| C14-PUB-VA | case14 | published | bus voltage angle | 0.05 | 0.0171 | degree | PASS |
| C14-PUB-QG | case14 | published | generator reactive output | 0.1 | 1.68 | MVAr | FAIL |
| C14-PUB-PG | case14 | published | slack generator active output | 0.1 | 0.00673 | MW | PASS |
| C14-PUB-LOSS | case14 | published | total active loss, sum of Pg minus sum of Pd | 0.1 | 0.00673 | MW | PASS |
<!-- /TABLE -->

### What the table says

- **pandapower agrees with an independent solver** (a polar Newton-Raphson in numpy, `validation/independent_nr.py`, no
  shared code) to 1e-13 on both cases for voltages, branch flows and losses. The solver itself is therefore sound on these
  data, and the choices that could matter (placeholder base kV, initialisation, solver tolerance) do not move the result
  (`results/sensitivity_and_hand_check.txt`).
- **14-bus against the published solution: not fully inside the tolerances written in advance.** Angles, slack output and
  total loss pass. Voltage magnitude fails at bus 4 only (published 1.019, computed 1.0177, a 1.329e-3 pu difference against a
  1.0e-3 tolerance), and generator reactive output fails by up to 1.675 MVAr (generator 3: published 23.4, computed 25.075).
  Because two independent solvers agree with each other and not with the printed solution, the difference lies between the
  printed solution and the case data it came with, not in pandapower. I tried three deliberate changes to the data
  (`validation/diagnose_14bus.py`); none improves the match, so the cause is **NOT SOURCED**. The tolerance was not widened
  to hide this. Criteria revision A is kept on the author's decision. The misses are open findings F-001 and F-002 in `validation/findings.json`, and `tests/test_validation.py` fails if either deviation changes in either direction.
- **9-bus against a published solution table: PASS.** Anderson and Fouad, *Power System Control and Stability*, 2nd ed., Fig. 2.19 (p. 38), typed in the book's bus numbering into `inputs/LV12/case9_published.csv` (the harness maps it to MATPOWER's numbering by load): worst voltage 3.69e-4 pu against 0.001, worst angle 0.035 degree against 0.05.
- **pandapower's bundled `case9` is not the Anderson and Fouad operating point.** Its generator set-points are all 1.0 pu; the
  MATPOWER file has 1.04, 1.025 and 1.025. The two solve to voltages 0.04 pu apart, which is why D-BUNDLED fails on case9. The
  validation here uses the data read from the MATPOWER files. Bundled `case14` equals the MATPOWER data to 1e-13.
- **The case file's slack output (72.3 MW) is a dispatch figure, not a solved one**: both solvers give 71.641 MW. It is reported as
  INFORMATIONAL because the case file does not say which columns are solved outputs.

## Sources

- MATPOWER `case9.m` and `case14.m`, https://github.com/MATPOWER/matpower/tree/master/data (fetched, SHA-256 pinned in
  `data/fetch_data.py`; not vendored, because MATPOWER's LICENSE says its case files are not covered by its BSD licence).
- The 14-bus published solution is the Vm, Va, Pg and Qg columns of `case14.m`, which MATPOWER states were converted from the IEEE
  Common Data Format file of the University of Washington Power Systems Test Case Archive. I could not open the Washington file;
  that the MATPOWER columns equal it is **NOT VERIFIED**.
- The 9-bus data come from Chow (ed.), *Time-Scale Modeling of Dynamic Networks*, Springer 1982, p. 70, as cited in `case9.m`.
  I have not read Chow or Anderson and Fouad, *Power System Control and Stability*.
- pandapower 3.5.6 (BSD-3-Clause), https://www.pandapower.org.

## Reproduce

```
pip install -r requirements.txt
python3 casefiles/fetch_data.py
python3 validation/run_validation.py          # prints and writes results/validation_results.json
python3 validation/sensitivity_and_hand_check.py
python3 validation/diagnose_14bus.py
python3 validation/make_table.py --readme     # refreshes the table above
python3 -m pytest -q                          # 20 tests
```

## Hand check (the approval step)

On the 9-bus case, branch 8-2 is a lossless transformer with x = 0.0625 pu. From the bus voltages alone,
P = V8 x V2 x sin(theta2 - theta8) / x x 100 MVA = 163.0000 MW, which equals pandapower's flow and generator 2's output
(`results/sensitivity_and_hand_check.txt`; voltages and angles in `results/case9_bus_results.csv`).

## Layout

`data/` fetch script and pinned hashes; `validation/` criteria, readers, the independent solver and the runners;
`tests/`; `results/` outputs of the last run; `.github/workflows/validate.yml` runs the tests in CI.
