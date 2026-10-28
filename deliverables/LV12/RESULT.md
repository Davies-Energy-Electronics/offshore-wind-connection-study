# LV12 - Connection study 1 of 4: repository, and pandapower validated against IEEE 9-bus and 14-bus

## Answer
Partly. pandapower solves both cases correctly: it agrees with an independent Newton-Raphson solver to better than 1e-12 on voltages, flows and losses [calc: connection-study/results/validation_results.json]. Against the published solutions it reproduces the 14-bus angles, slack output and total loss inside the tolerances written in advance, but it misses two of them: bus 4 voltage magnitude by 1.329e-3 pu against 1.0e-3 pu, and generator reactive output by up to 1.675 MVAr against 0.1 MVAr [calc: connection-study/results/validation_results.json]. The 9-bus published-solution comparison, added on 28 October 2026 against Anderson and Fouad (Fig. 2.19), passes both tolerances (see the addendum) [calc: connection-study/results/validation_results.json].

One question was asked and one answered. The repository is prepared in `connection-study/` and is not public; only Jack makes it public.

## Assumptions
- Data are the MATPOWER `case9.m` and `case14.m` files, pinned by hash in `connection-study/data/fetch_data.py`, not vendored. [src: MATPOWER repository, data directory]
- `case14.m` has no base voltage; a placeholder of 132 kV is used. Per-unit results do not depend on it: changing it to 33 kV or 345 kV moves no result by more than 1e-12 [calc: connection-study/results/sensitivity_and_hand_check.txt].
- Generator reactive limits are not enforced, matching the printed solutions. [calc: connection-study/validation/criteria.json]
- The published 14-bus solution is the Vm, Va, Pg and Qg columns of `case14.m`, which MATPOWER says were converted from the University of Washington archive file. That the columns equal the Washington file is NOT VERIFIED. [src: header of case14.m]
- 9-bus data are from Chow 1982 p. 70 as cited in `case9.m`; Chow and Anderson and Fouad were not read. [src: header of case9.m]
- pandapower version 3.5.6, numpy 2.4.6. [calc: connection-study/results/validation_results.json]

## Acceptance criteria
Written and committed before the first run, in their own commit (revision A). [test: connection-study/validation/criteria.json]

- Published comparison: twice the half-unit of the last printed digit. Voltage magnitude 1.0e-3 pu, angle 0.05 degree, generator reactive output 0.1 MVAr, slack output 0.1 MW, total loss 0.1 MW. [test: connection-study/validation/criteria.json]
- Solver to solver: voltage 1e-6 pu, angle 1e-4 degree, flows and loss 1e-4 MW or MVAr. [test: connection-study/validation/criteria.json]
- The 9-bus published table is OPEN until supplied; the case-file generator figures are informational only. [test: connection-study/validation/criteria.json]

## Tolerance table (from the last run)
The same table is in the repository README. [calc: connection-study/results/tolerance_table.md]

## Independent check
- A second solver, `connection-study/validation/independent_nr.py`, written separately from pandapower, reproduces every pandapower voltage, branch flow and loss on both cases. Worst voltage difference 6.66e-16 pu, worst flow difference 7.11e-13 MW or MVAr. [calc: connection-study/results/validation_results.json]
- Energy balance on the 14-bus case holds to 1e-6 MW. [test: connection-study/tests/test_validation.py]
- Sensitivity on the two least certain set-up choices (placeholder base voltage; initialisation and solver tolerance) moves no 14-bus voltage by more than 5.74e-9 pu. [calc: connection-study/results/sensitivity_and_hand_check.txt]
- Diagnosis of the 14-bus misses: three deliberate data changes (shunt removed, taps inverted, line charging removed) all fit the printed solution worse. Cause of the difference between the printed solution and its own data: NOT SOURCED. [calc: connection-study/results/diagnose_14bus.txt]
- Tests: 20 passed, run from a clean shell with `python3 -m pytest -q` in `connection-study/`. [test: connection-study/tests/test_validation.py]

## Findings
- pandapower's bundled `case9` sets every generator voltage to 1.0 pu, where the MATPOWER file has 1.04, 1.025 and 1.025; the two solve 0.04 pu apart in voltage. Anyone using `pn.case9()` for this check solves a different operating point. [calc: connection-study/results/validation_results.json]
- The slack output in the 9-bus case file is a dispatch value: both solvers give 71.641 MW, the file says 72.3 MW. [calc: connection-study/results/validation_results.json]
- F-001 (open): the 14-bus voltage miss is bus 4 only, 1.329e-3 pu; every other voltage is within 5e-4 pu. Cause NOT SOURCED. [calc: connection-study/validation/findings.json]
- F-002 (open): the 14-bus reactive output differs from the printed solution at all five generators, by 0.22 to 1.68 MVAr. Cause NOT SOURCED. [calc: connection-study/validation/findings.json]
- F-003 (closed 28 Oct 2026): the 9-bus comparison against Anderson and Fouad, Fig. 2.19, passes; see the addendum. [calc: connection-study/validation/findings.json]
- Criteria revision A is kept unchanged on Jack's decision. `tests/test_validation.py` fails if either 14-bus deviation changes, in either direction, or if a revision A tolerance is edited. [test: connection-study/tests/test_validation.py]

## Hand check for Jack (the approval step)
Branch 8-2 on the 9-bus case is a lossless transformer with reactance 0.0625 pu. Compute V8 x V2 x sin(theta2 - theta8) / 0.0625 x 100 MVA from the bus voltages in `connection-study/results/case9_bus_results.csv`; it gives 163.0000 MW, equal to pandapower's flow and to generator 2's output. [calc: connection-study/results/sensitivity_and_hand_check.txt]

## Decisions for Jack
- Decided by Jack: keep criteria revision A; the 14-bus misses are recorded as open findings F-001 and F-002 with cause NOT SOURCED, and no tolerance is widened.
- Supplied 28 Oct 2026: the 9-bus published table (Anderson and Fouad, Fig. 2.19) is in `inputs/LV12/case9_published.csv` [src: Anderson and Fouad, 2nd ed., Fig. 2.19, p. 38]. Until then C9-PUB stays OPEN.
- Make the repository public yourself when you are satisfied. I did not create a public repository.

## Sources
- MATPOWER case files and LICENSE note, https://github.com/MATPOWER/matpower. [src: raw.githubusercontent.com/MATPOWER/matpower/master/data]
- pandapower documentation of `case9` and `case14` (data origin PYPOWER; `case9` attributed to Anderson and Fouad). [src: pandapower 3.5.6 docstrings, power_system_test_cases.py]
- Not reachable in this session, so not used as sources: the University of Washington archive and a textbook table. A search-result summary of 9-bus voltages was not treated as a source.

## Other questions this raised, not answered here
- Which bus voltage and reactive figures does the Washington archive print for the 14-bus case, and do they equal the MATPOWER columns?
- Does the 14-bus difference come from the original program's convergence or from rounded branch data? Needs the original file.

## Limits
- The 14-bus "published solution" is read through MATPOWER, not from the Washington file. NOT VERIFIED.
- Nothing here validates pandapower's short-circuit or protection functions; those belong to the later blocks of the study.

## Gate
- Kind: calc
- Prepared: lev-portfolio agent, 18 October 2026, on Jack's explicit Sunday override of the rest-day rule
- Checked: independent solver `connection-study/validation/independent_nr.py` and the test suite, evidence in Independent check above; no second agent has read it as a sceptical reviewer
- Approved: pending Jack

## Addendum, 28 October 2026 (Claude)
- **Reproducibility fixed.** The case files were fetched into `data/`, which the workbench ignores, so `data/fetch_data.py` was never committed and the tests could not run from a clean clone. The folder is now `casefiles/`, with a new `fetch_data.py` that downloads `case9.m` and `case14.m` from MATPOWER and refuses them unless their SHA-256 matches the hashes pinned on 28 Oct 2026. Rerun from a clean shell: 20 of 20 tests pass, and every result reproduces to floating-point noise [calc: deliverables/LV12/connection-study/results/validation_results.json].
- **9-bus against a secondary published table (informational).** KIOS Centre, 'IEEE 9-bus modified test system', model documentation R0 (2020), Table 6, compared there with a PSS/E version of the benchmark [src: www2.kios.ucy.ac.cy/testsystems, IEEE9_model_documentation_R0.pdf]. Buses mapped by load, not by result (WSCC 5, 6, 7, 8, 9 = MATPOWER 9, 5, 8, 7, 6). Worst angle difference 0.0048 degree against the 0.05 degree tolerance; every magnitude within the 0.005 pu a two-decimal print covers [calc: deliverables/LV12/connection-study/results/compare_9bus_secondary.txt]. This is not the Anderson and Fouad table the criteria name, so C9-PUB stays OPEN until Jack either supplies that table or accepts this source in its place.
- **Ready for the textbook table (28 Oct 2026, Jack's decision: use Anderson and Fouad, the source the criteria name).** The harness now also takes the book's own bus numbering (`wscc_bus`), mapped to MATPOWER's by load, and ignores an unfilled template. Template and steps: `inputs/LV12/case9_published.TEMPLATE.csv` and `inputs/LV12/README_case9_published.md`. A trial with the secondary table's values gave C9-PUB-VA PASS (0.0048 degree) through the mapping [calc: deliverables/LV12/connection-study/results/compare_9bus_secondary.txt]; the trial file was removed, so C9-PUB stays OPEN until the book's values are typed in. The agent cannot supply the book: no legitimate copy was reachable in the session.
- **C9-PUB closed, 28 Oct 2026.** Jack supplied the textbook. The nine-bus prefault load flow, Anderson and Fouad, *Power System Control and Stability*, 2nd ed., Fig. 2.19, p. 38, was typed into `inputs/LV12/case9_published.csv` in the book's bus numbering [src: Anderson and Fouad, 2nd ed., Fig. 2.19, p. 38]. Against it pandapower gives C9-PUB-VM PASS, worst 3.69e-4 pu against 0.001 pu, and C9-PUB-VA PASS, worst 0.035 degree against 0.05 degree [calc: deliverables/LV12/connection-study/results/validation_results.json]. The book prints angles to 0.1 degree, so the criteria's 0.05 degree is stricter than its own half-unit rule would set; it still passes. 20 tests pass, one skipped by design (the no-table case) [test: deliverables/LV12/connection-study/tests/test_validation.py]. Findings F-001 and F-002 (14-bus) stay open with cause NOT SOURCED, as Jack decided; F-003 is closed.
