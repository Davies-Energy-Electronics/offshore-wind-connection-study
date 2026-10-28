# LV15 - Connection study 4 of 4: N-1, single-line diagram, report

## Answer
The final base design is **revision D** [test: deliverables/LV15/connection-study/model/criteria_D.json]: two 155 MVAr onshore reactor units, a 630 mm2 export cable and a 1000 mm2 array cable sized on soil 1.5 K m/W, and the string relay R1 at 960 A. Intact, all four cases are inside limits [calc: deliverables/LV15/connection-study/results/n1_D.json]. It is **not N-1 secure at full output**: one export circuit, offshore transformer or onshore transformer out curtails C1 to 246.1, 248.4 and 239.8 MW; a string outage rides through in all cases; one reactor unit out rides through at full output and leaves only light load (C4) over voltage, PCC 1.0651 pu [calc: deliverables/LV15/connection-study/results/n1_D.json]. Revision C, run first, is kept below as the step that found the three remedies. Everything is a self-directed study on ASSUMED data; no standard, grid code or SQSS was read.

The single-line diagram is results/sld.png (revision D; results/sld_C.png for revision C) and the report results/LV15_connection_study_report.pdf (eleven pages, short of the length the task named: nothing was added to fill pages) [calc: deliverables/LV15/connection-study/results/LV15_connection_study_report.pdf]. Nothing is public: publication is LVD1.

## Revision D (final), 28 October 2026
- Approvals: D1 to D4 approved by Jack, 28 Oct 2026; D5 to D7 taken on his instruction to finalise with the improvements, each shown first on revision C [test: deliverables/LV15/connection-study/model/criteria_D.json].
- D5 array 1000 mm2 (863.3 A against 796.0 A); D6 reactor as two 155 MVAr units; D7 R1 pickup 960 A [calc: deliverables/LV15/connection-study/results/n1_D.json].
- Checks: SOLVE FAIL (one onshore transformer out at C3, full output, does not converge; counted as outside limits); BAL PASS; HAND-O2 PASS (248.4 MW against 250 MW); FAULT-D PASS (0.266 percent); R1 PASS (pickup window 952.9 to 5540.3 A, 0.4435 s to R2) [calc: deliverables/LV15/connection-study/results/checks_D.json].
- Tests: 13 of 13 on revisions C and D [calc: deliverables/LV15/connection-study/results/tests.txt].

## Revision C (the step), decisions D1 to D4 (approved by Jack, 28 Oct 2026)
Recorded in model/criteria_C.json, committed before any LV15 run (commit 34caf6a) [test: deliverables/LV15/connection-study/model/criteria_C.json]:
- D1: size cables on soil 1.5 K m/W until a survey replaces it: array 800 mm2 (790.3 A against 785.7 A), export 630 mm2 (745.9 A against 738.9 A) [calc: deliverables/LV15/connection-study/results/n1.json].
- D2: LV13 revision C uses the sized cables' resistance and capacitance; reactance and lengths unchanged.
- D3: the minimum-fault ordering check joins the grading pass rule; R4 TMS 0.35; its 3.9 s backup time is reported as a finding [calc: deliverables/LV14/connection-study/results/grading.txt].
- D4: no datasheets or survey exist; every input stays ASSUMED.

## Assumptions
Every input is ASSUMED or DESIGN, none sourced to a datasheet or standard: LV13's table A01 to A19 [calc: deliverables/LV13/RESULT.md] and LV14's cable inputs [calc: deliverables/LV14/connection-study/model/cable.py], with soil thermal resistivity 1.5 K m/W instead of 1.0 (D1). NOT SOURCED.

## Acceptance criteria
Written and committed before the first run [test: deliverables/LV15/connection-study/model/criteria_C.json]: voltages PCC 0.95 to 1.05 pu and internal 0.90 to 1.10 pu; cable and transformer loading at most 100 percent; an outage RIDES THROUGH if inside limits at the case's output, otherwise the largest output inside limits is found by bisection to 1 MW (CURTAILED); a run that does not converge is outside limits. Author's criteria, NOT SOURCED to the Grid Code or SQSS.

## Intact network, revision C
| Case | Loss MW | PCC pu | V max pu | Export A | Array first A | Max cable % | Exceptions | Source |
|---|---|---|---|---|---|---|---|---|
| C1 | 9.178 | 0.99 | 1.0 | 605.3 | 712.9 | 90.2 | 0 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| C2 | 10.117 | 0.9534 | 1.0366 | 704.8 | 725.4 | 94.5 | 0 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| C3 | 10.609 | 1.0244 | 1.05 | 595.3 | 796.0 | 100.7 | 5 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| C4 | 0.706 | 1.0479 | 1.0624 | 394.9 | 77.6 | 52.9 | 0 | [calc: deliverables/LV15/connection-study/results/n1.json] |

## N-1
| Outage | Case | Verdict | Export A | Max trafo % | PCC pu | Source |
|---|---|---|---|---|---|---|
| O1 | C1 | CURTAILED: 246.9 MW | 1134.7 | 97.6 | 0.9748 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O1 | C2 | OUTSIDE LIMITS even at zero output | 1233.5 | 86.8 | 0.9395 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O1 | C3 | CURTAILED: 255.5 MW | 1320.0 | 120.8 | 1.0063 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O1 | C4 | RIDES THROUGH | 415.5 | 31.9 | 1.035 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O2 | C1 | CURTAILED: 247.7 MW | 579.8 | 171.1 | 0.9834 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O2 | C2 | OUTSIDE LIMITS even at zero output | 669.2 | 165.4 | 0.9485 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O2 | C3 | CURTAILED: 234.4 MW | 757.1 | 230.8 | 1.0057 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O2 | C4 | RIDES THROUGH | 394.6 | 17.7 | 1.0479 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O3 | C1 | CURTAILED: 239.1 MW | 619.1 | 178.5 | 0.9829 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O3 | C2 | OUTSIDE LIMITS even at zero output | 706.1 | 165.9 | 0.9482 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O3 | C3 | CURTAILED: 215.6 MW | None | None | None | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O3 | C4 | RIDES THROUGH | 392.4 | 18.0 | 1.0479 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O4 | C1 | RIDES THROUGH | 526.2 | 66.2 | 0.9931 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O4 | C2 | RIDES THROUGH | 618.7 | 66.9 | 0.9537 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O4 | C3 | RIDES THROUGH | 455.4 | 74.0 | 1.0317 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O4 | C4 | RIDES THROUGH | 387.0 | 8.4 | 1.0474 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O5 | C1 | OUTSIDE LIMITS even at zero output | 592.8 | 90.3 | 1.027 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O5 | C2 | CURTAILED: 46.1 MW | 697.1 | 106.3 | 0.9884 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O5 | C3 | OUTSIDE LIMITS even at zero output | 508.0 | 77.4 | 1.0643 | [calc: deliverables/LV15/connection-study/results/n1.json] |
| O5 | C4 | VOLTAGE EXCEPTION (not curable by curtailment) | 445.8 | 68.0 | 1.084 | [calc: deliverables/LV15/connection-study/results/n1.json] |

Outages as defined in criteria_C.json: one export circuit, one offshore transformer, one onshore transformer, the first section of string 1, the reactor [test: deliverables/LV15/connection-study/model/criteria_C.json].

## Independent check
The checks written in criteria_C.json, plus an independent re-derivation of the LV14 numbers LV15 builds on [calc: deliverables/LV14/independent_check/check.py]:
- SOLVE: FAIL. One run does not converge (one onshore transformer out, C3, full output); counted as outside limits [calc: deliverables/LV15/connection-study/results/checks.json].
- BAL: PASS, worst 4.0e-09 MW [calc: deliverables/LV15/connection-study/results/checks.json].
- HAND-O1: FAIL. The rule assumed the remaining export circuit carries the intact total; it carries 1134.7 A against 2 x 605.3 A (6.27 percent), because half the charging current leaves with the circuit that is out. Reported as failed, not adjusted [calc: deliverables/LV15/connection-study/results/checks.json].
- HAND-O2: PASS, 247.7 MW against 250 MW by hand (0.92 percent) [calc: deliverables/LV15/connection-study/results/checks.json].
- FAULT-C: PASS, largest change 0.14 percent, so LV14's grading verdicts stand [calc: deliverables/LV15/connection-study/results/checks.json].
- New finding: R1's pickup of 950 A is below 1.2 times the revision C array load (796.0 A, so 955.2 A); set R1 to at least 960 A [calc: deliverables/LV15/connection-study/results/n1.json].
- Tests: 8 of 8 from a clean shell with ./run_all.sh [calc: deliverables/LV15/connection-study/results/tests.txt]; LV13 and LV14 tests rerun and pass.

## What-ifs (labelled, chosen after the results)
- W3: array re-sized on the revision C design current: 1000 mm2; all four intact cases inside limits [calc: deliverables/LV15/connection-study/results/checks.json].
- W4: reactor as two 155 MVAr units, one out: C1 to C3 inside limits, C4 over [calc: deliverables/LV15/connection-study/results/checks.json].

## Limits
Self-directed study on assumed data; not professional experience; not reviewed by a chartered engineer. Steady state only: no dynamics, harmonics, earth faults or economics. Taps fixed; turbines fixed P and Q.

## Sources
No standard, grid code, datasheet or survey was read; nothing is cited as read. pandapower 3.5.6 was used [calc: deliverables/LV14/connection-study/requirements.txt].

## Gate
- Kind: calc
- Prepared: Claude, 27 and 28 October 2026, criteria first in commits 34caf6a (C) and df09ba4 (D)
- Checked: 8 tests, energy balance, two hand checks (one failed, reported), fault re-check on revision C, and an independent re-derivation of LV14's export rating and 66 kV fault level (deliverables/LV14/independent_check/check.py, ALL PASS); same author as LV15, so no second agent has reviewed LV15 itself
- Approved: pending Jack for the study and the report (his decisions D1 to D4 recorded 2026-10-28); publication is LVD1
