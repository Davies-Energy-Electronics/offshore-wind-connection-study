# LV14 - Connection study 3 of 4: cable sizing, fault levels and overcurrent grading

## Answer
On the revision B base design (LV13 plus the 310 MVAr onshore reactor in all four cases), the smallest standard copper conductors that carry the design current are **630 mm2 for the 66 kV array cables (814 A against 786 A, 3.6 percent margin)** and **500 mm2 for each 220 kV export circuit (760 A against 739 A, 2.8 percent margin)** [calc: deliverables/LV14/connection-study/results/cable_sizing.txt]. Fault levels at five busbars range from 7.5 to 17.1 kA at maximum (400 kV PCC 15.1 kA, 66 kV offshore bus 17.1 kA) [calc: deliverables/LV14/connection-study/results/faults.txt]. Four relays grade with at least 0.30 s margin at the maximum faults [calc: deliverables/LV14/connection-study/results/grading.txt], but one ordering fault appears at the minimum fault (see Findings). Everything is a self-directed study on ASSUMED data. **No standard was read**: IEC 60287, 60909, 60255-151 and 60228 are named for the method only, and every formula is written from general knowledge and is NOT SOURCED to the standard text.

One question was asked and one answered. LV15 (N-1 and the single-line diagram) is not done here. Branch note: the session was told to work on `claude/lv14-cable-sizing-kaihyx`; the brief named `agent/LV14`. Work is committed locally as `agent/LV14` and pushed to the `claude/` branch.

## Basis: revision B
Decision 7 (Jack, 21 Oct 2026): build on LV13 revision B, with 310 MVAr of reactor compensation in the base design. Revision B is this: LV13's model unchanged, with a 310 MVAr reactor at the 220 kV onshore bus in every case, called through the LV13 builder (`model/revb.py`). Revision A of LV13 is untouched. LV14 criteria were written and committed before any number was run [test: deliverables/LV14/connection-study/model/criteria_B.json]. The revision B load flow gives the design currents: array first section 785.7 A (C3), export circuit 738.9 A (C2) [calc: deliverables/LV14/connection-study/results/design_currents.json]. C4 still has its PCC voltage 1.0521 pu, over 1.05 [calc: deliverables/LV14/connection-study/results/design_currents.json]; LV13's what-if said the same.

## Assumptions
Every input is ASSUMED or DESIGN; none is sourced to a datasheet or standard. Full values: [calc: deliverables/LV14/connection-study/model/cable.py] (cable inputs) and [calc: deliverables/LV14/connection-study/model/faults.py] (grid, wind, c factors); the LV13 table A01 to A19 still applies [calc: deliverables/LV13/RESULT.md]. Cable inputs: copper, 90 C conductor, 15 C seabed, soil 1.0 K m/W, depth 1.0 m, XLPE 10 mm (66 kV) and 24 mm (220 kV), sheath and armour loss 10 percent. NOT SOURCED. Fault inputs: grid 10000 MVA maximum and 5000 MVA minimum with X/R 10, wind 1.1 times rated current. NOT SOURCED.

## Acceptance criteria
Written and committed before the first run, in their own commit (014f7e6) [test: deliverables/LV14/connection-study/model/criteria_B.json]: smallest size in the series that meets the design current; fault levels by the voltage-source method checked within 0.1 percent; grading with pickup at 1.2 times load and at most 0.8 times minimum fault, and 0.30 s margin at the maximum fault. The 0.30 s margin and the series are NOT SOURCED.

## 1. Cable sizing
Method: a one-dimensional thermal circuit, the form IEC 60287 uses. Heat from each core crosses its own insulation (T1), then all three cores' heat crosses the coverings (T3) and the soil (T4):

`I = sqrt( (dtheta - 0.5 Wd T1 - 3 Wd (T3+T4)) / (R T1 + 3 R (1+lam) (T3+T4)) )` (form written from general knowledge, NOT SOURCED to IEC 60287) [calc: deliverables/LV14/connection-study/model/cable.py]

Inputs (all ASSUMED, NOT SOURCED): copper, 90 C conductor, 15 C seabed, soil 1.0 K m/W, buried 1.0 m, XLPE insulation 10 mm (66 kV) and 24 mm (220 kV), XLPE 3.5 K m/W, coverings 16 mm at 6.0 K m/W, sheath and armour loss 10 percent, skin and proximity constants 1.0 and 0.8, tan delta 0.001 [calc: deliverables/LV14/connection-study/model/cable.py] [calc: deliverables/LV14/connection-study/model/size.py]. Size series is general knowledge of IEC 60228 (not read).

| Cable | Design A | Chosen | Rating A | Margin | R at 90 C (ohm/km) | LV13 assumed R | Source [calc: deliverables/LV14/connection-study/results/cable_sizing.txt] |
|---|---|---|---|---|---|---|---|
| 66 kV array | 785.7 | 630 mm2 | 814.0 | 3.6 percent | 0.0392 | 0.040 (A07) | [calc: deliverables/LV14/connection-study/results/cable_sizing.txt] |
| 220 kV export | 738.9 | 500 mm2 | 759.6 | 2.8 percent | 0.0464 | 0.022 (A11) | [calc: deliverables/LV14/connection-study/results/cable_sizing.txt] |

[calc: deliverables/LV14/connection-study/results/cable_sizing.txt]

**Whiteboard version** (the full steps are in [calc: deliverables/LV14/connection-study/results/worked_example.txt]): 75 K available (90 minus 15); R at 90 C 46.37 uohm/m; T1 0.5784, T3 0.1740, T4 0.4828 K m/W; dielectric loss 0.679 W/m per core; numerator 73.466, denominator 1.2732e-04, I = sqrt(73.466 / 1.2732e-04) = 759.6 A [calc: deliverables/LV14/connection-study/results/worked_example.txt]. In words: how many watts per metre the soil path can carry away for 75 K, divided by the heat each ampere makes.

Sensitivity: with soil at 1.5 K m/W the chosen sizes rate 712 A (array) and 667 A (export), both under the design current, and the smallest sizes that pass become 800 mm2 (array) and 630 mm2 (export); with soil at 2.0 K m/W they become 1200 mm2 and 800 mm2 [calc: deliverables/LV14/connection-study/results/cable_sizing.txt]. The 2.8 and 3.6 percent margins are therefore thin against the least certain input, the soil. A site survey or datasheet is the first thing to replace.

Short-circuit withstand (adiabatic, K 143 NOT SOURCED): array needs at least 55.8 mm2 for the R1 clearing time, export at least 64.2 mm2 for the R3 time, so the current rating, not the fault, sets both sizes [calc: deliverables/LV14/connection-study/results/grading.txt].

Informational, not an LV14 result: if one export circuit is out, the other carries about 1478 A (twice 739 A), above the rating of every size in the series up to 2000 mm2 [calc: deliverables/LV14/connection-study/results/cable_sizing.txt]. That is the LV15 question.

### Consistency with LV13 (what-if W2, informational)
The export cable LV13 assumed (R 0.022, 1000 A) is a 1000 mm2 cable, but the load only needs 500 mm2, which has twice the resistance. Re-running revision B with the sized R and charging capacitance and the sized ratings [calc: deliverables/LV14/connection-study/results/whatif_w2.txt]: array loading 85 to 95 percent, export loading 76 to 98 percent (C2 97.9 percent), losses 10.0 to 11.5 MW at full output against 4.9 to 6.6 MW in LV13 revision A, PCC voltage C1 0.9952, C2 0.9583, C3 1.0301, C4 1.0527 pu. So the minimum-size cable roughly doubles losses. Whether to pay for a larger cable is an economic question not asked here: NOT ASSESSED. The base design (LV13 values) is not changed.

## 2. Fault levels (IEC 60909 voltage-source method, as coded in pandapower 3.5.6)
Maximum: three-phase, c 1.10, grid 10000 MVA (LV13 A15), everything in service, wind farm at ASSUMED 1.1 times rated current per turbine, added arithmetically. Minimum: two-phase, c 1.00, grid 5000 MVA, no wind. Transformer correction K_T = 0.95 cmax/(1+0.6 xT) in the maximum case only; read in pandapower's source code (`build_branch._transformer_correction_factor`) [test: deliverables/LV14/connection-study/model/faults.py].

| Busbar | kV | Ik'' max (kA) | of which grid only | peak ip (kA) | Ith 1 s (kA) | MVA | Ik'' min 3ph (kA) | Ik'' min 2ph (kA) | Source [calc: deliverables/LV14/connection-study/results/faults.txt] |
|---|---|---|---|---|---|---|---|---|---|
| PCC | 400 | 15.07 | 14.43 | 36.5 | 15.32 | 10440 | 7.22 | 6.25 | [calc: deliverables/LV14/connection-study/results/faults.txt] |
| Onshore 220 kV | 220 | 8.76 | 7.60 | 21.8 | 9.09 | 3337 | 5.47 | 4.74 | [calc: deliverables/LV14/connection-study/results/faults.txt] |
| Offshore 220 kV | 220 | 7.46 | 6.31 | 17.9 | 7.65 | 2843 | 4.70 | 4.07 | [calc: deliverables/LV14/connection-study/results/faults.txt] |
| Offshore 66 kV | 66 | 17.07 | 13.23 | 40.3 | 17.65 | 1952 | 10.44 | 9.04 | [calc: deliverables/LV14/connection-study/results/faults.txt] |
| End of string 1 (S1T8) | 66 | 12.72 | 9.76 | 27.2 | 12.87 | 1454 | 7.98 | 6.91 | [calc: deliverables/LV14/connection-study/results/faults.txt] |

[calc: deliverables/LV14/connection-study/results/faults.txt]

Gaps: single-phase earth faults NOT DONE (needs zero-sequence and earthing data nobody has assumed). The 400 kV figure of 15.07 kA is a model output of the assumed 10 GVA grid; the real value would come from the network operator. The wind contribution is checked by hand: 40 turbines x 1.1 x 10 MVA over root three x 66 kV is 3.85 kA, the difference between the total and grid-only columns at the 66 kV bus [test: deliverables/LV14/connection-study/tests/test_lv14.py].

Check: pandapower against a separate impedance-matrix calculation in numpy (grid only, maximum, minimum 3ph and 2ph) differs by at most 1.2e-12 percent against the 0.1 percent tolerance [calc: deliverables/LV14/connection-study/results/faults.json]. Honest limit: both implement the same method, so this checks the model build and arithmetic, not the standard. The hand value at the PCC, 10000 MVA over root three x 400 kV = 14.434 kA, equals the grid-only figure [test: deliverables/LV14/connection-study/tests/test_lv14.py].

## 3. Overcurrent grading
[calc: deliverables/LV14/connection-study/model/grading.py] Chain, from the string to the grid: R1 string feeder breaker (66 kV), R2 OSS transformer LV incomer (66 kV), R3 export circuit at the onshore end (220 kV), R4 onshore transformer HV side (400 kV). Curve: IEC standard inverse, t = TMS x 0.14 / ((I/Is)^0.02 - 1); the constants come from relay-vendor documentation shown in a search summary, the pages could not be opened and the standard was not read: NOT VERIFIED. Currents come from the grid-only network solution; wind adds only to R1 (0.77 kA per string). Directional and instantaneous elements, CT saturation, inrush, differential and earth-fault protection are NOT assessed.

| Relay | Max load (A) | Pickup Is (A) | TMS | Min fault at zone end (A) | Source [calc: deliverables/LV14/connection-study/results/grading.txt] |
|---|---|---|---|---|---|
| R1 string feeder (66 kV) | 785.7 | 950 | 0.100 (design choice) | 6910 | [calc: deliverables/LV14/connection-study/results/grading.txt] |
| R2 OSS transformer LV (66 kV) | 1960.1 | 2400 | 0.100 | 4522 | [calc: deliverables/LV14/connection-study/results/grading.txt] |
| R3 export circuit (220 kV) | 738.9 | 900 | 0.125 | 2037 | [calc: deliverables/LV14/connection-study/results/grading.txt] |
| R4 onshore transformer HV (400 kV) | 326.5 | 400 | 0.225 | 1303 | [calc: deliverables/LV14/connection-study/results/grading.txt] |

Pickup rule met by all (1.2 x load, at most 0.8 x minimum fault) [calc: deliverables/LV14/connection-study/results/grading.txt]. Margins at the maximum faults (rule: 0.30 s): R1 0.239 s then R2 0.684 s (0.444 s margin) for a fault beyond R1; R3 1.098 s (0.415 s) and R4 1.554 s (0.455 s) [calc: deliverables/LV14/connection-study/results/grading.txt]. At the 220 kV offshore busbar R3 trips at 0.689 s and R4 at 1.058 s (0.369 s margin) [calc: deliverables/LV14/connection-study/results/grading.txt]. Chart: [calc: deliverables/LV14/connection-study/results/grading_chart.png] (points in grading_points.csv).

R1 has no downstream relay in this study, so its TMS of 0.100 is a design choice that criteria_B.json did not fix. The grading recomputed independently in the test file passes [test: deliverables/LV14/connection-study/tests/test_lv14.py].

## Independent check
- Cable rating: re-derived step by step in a separate worked-example script and in the test file, 0.5 percent tolerance [test: deliverables/LV14/connection-study/tests/test_lv14.py].
- Fault levels: pandapower against a numpy impedance-matrix calculation, tolerance 0.1 percent [test: deliverables/LV14/connection-study/tests/test_lv14.py].
- Grading: operating times and margins recomputed from the saved settings [test: deliverables/LV14/connection-study/tests/test_lv14.py].
- Tests: all passed, from a clean shell with `./run_all.sh` [calc: deliverables/LV14/connection-study/results/tests.txt]. Same author throughout: no second agent has reviewed it.

## Findings
- **Ordering fault at the minimum fault.** For a two-phase fault at the end of a string with the grid at 5000 MVA, R3 would take 6.19 s and R4 4.43 s, so the onshore transformer relay would trip before the export circuit relay [calc: deliverables/LV14/connection-study/results/grading.txt]. This check was added after seeing the chart; it is not in the rules written in advance, which pass. Setting R4 to TMS 0.35 restores at least 0.30 s margin at every minimum fault (R4 at 6.89 s) but slows R4 at the maximum fault (3.9 s for an offshore 66 kV busbar fault, against 1.55 s) [calc: deliverables/LV14/connection-study/results/grading.txt]. Whether a 3.9 s backup time is acceptable is not settled here.
- The curves for R3 and R4 cross near 4 kA referred to 66 kV, which is where the ordering fault comes from: the pickups (900 A at 220 kV, 400 A at 400 kV) sit at different multiples of the fault current [calc: deliverables/LV14/connection-study/results/grading_chart.png].
- One OSS transformer out of service: R2 would see 9.65 kA and trip in 0.50 s for an OSS 66 kV busbar fault [calc: deliverables/LV14/connection-study/results/grading.txt]. Informational.
- The minimum-size cables roughly double the losses relative to the LV13 values (above).

## Hand check for Jack (the approval step)
Work the export cable rating on paper from `results/worked_example.txt` (10 lines). Then check one fault level by hand: on 100 MVA, the 66 kV bus sees in series the grid 0.0011 + j0.01095 pu (c 1.1 x 100/10000 split at X/R 10), two onshore transformers in parallel 0.000578 + j0.02699 pu (14 percent on 500 MVA, K_T 0.964), the two export circuits in parallel 0.001364 + j0.007748 pu (0.66 + j3.75 ohm over 484 ohm), and two OSS transformers 0.000578 + j0.02699 pu. The sum is 0.00362 + j0.07268 pu, |Z| 0.07277 pu. Ik'' = 1.1 x (100 / (root three x 66)) / 0.07277 = 1.1 x 0.8748 / 0.07277 = 13.22 kA, against 13.23 kA grid-only at OSS66 in the model [calc: deliverables/LV14/connection-study/results/faults.txt]. Then defend the ASSUMED rows aloud, especially soil resistivity, burial depth, insulation thickness and the grid short-circuit level.

## Decisions for Jack
- Is the sizing margin acceptable [calc: deliverables/LV14/connection-study/results/cable_sizing.txt], or should the sizing rule carry a margin written into a revision C of the criteria?
- Revision C of LV13 with the sized cable data (W2 shows C4 still over its PCC limit) [calc: deliverables/LV14/connection-study/results/whatif_w2.txt]?
- Is the added minimum-fault check part of the pass rule from now on (then R4 needs a longer TMS) [calc: deliverables/LV14/connection-study/results/grading.txt]?
- Supply cable datasheets or a site survey in `inputs/LV14/` (none were supplied) to replace the ASSUMED rows.

## Sources
- No standard was read and none is cited as read. IEC 60287, IEC 60909, IEC 60255-151, IEC 60228 and the copper/XLPE constants (K 143, resistivity 1.7241e-8 ohm m, alpha 0.00393) are written from general knowledge: NOT SOURCED.
- pandapower, installed locally [calc: deliverables/LV14/connection-study/requirements.txt]; its IEC 60909 implementation, including the transformer correction factor and the c factors, was read in its source code.
- IEC curve constants (the two curve constants) were seen in search summaries of relay-vendor documents (OPAL-RT ARTEMiS documentation, Protecta relay manuals). Page fetches failed (host not found), so NOT VERIFIED (NOT SOURCED).
- A search result from the University of Southampton (Chatzipetros and Pilgrim) reports that IEC 60287 may overestimate large three-core cable temperatures; the page could not be opened, so this is not used for any number.

## Limits
- Self-directed study on assumed data. It is not professional experience and has not been reviewed by a chartered engineer.
- Intact network only; no mutual heating between circuits; no cable laying, burial depth variation or J-tube sections.
- Earth faults, protection beyond overcurrent, and cable and transformer thermal damage curves beyond the adiabatic check are not done.

## Gate
- Kind: calc
- Prepared: Claude Code (lev-portfolio), 22 October 2026, criteria first in commit 014f7e6
- Checked: 9 tests passed (`python3 -m pytest -q` in `connection-study/`), independent impedance-matrix fault check, hand-formula rating check; no second agent has reviewed it
- Approved: pending Jack

## Independent check, 27 October 2026 (Claude, not the LV14 author)
`independent_check/check.py` re-derives the hand-check numbers from the inputs stated in this file, without importing or reading the LV14 model code. All twelve values agree [calc: deliverables/LV14/independent_check/check.py]:
- Export cable, 500 mm2: conductor 26.31 mm, ys 0.0411, yp 0.0134, R at 90 C 46.367 uohm/m, T1 0.5784, T3 0.1740, T4 0.4828 K m/W, C 133.93 nF/km, Wd 0.679 W/m, rating 759.6 A, each within 0.12 percent.
- Offshore 66 kV bus, maximum, grid only: K_T 0.964, |Z| 0.07276 pu, Ik'' 13.226 kA against 13.226 kA, 0.004 percent.
- `run_all.sh` rerun from a clean shell: results reproduce to floating-point noise, 9 of 9 tests pass.
Limit: the check uses the same general-knowledge formulas, so it checks the arithmetic and the build, not the standard. The four decisions above are answered as proposals D1 to D4 in deliverables/LV15/connection-study/model/criteria_C.json; approval stays with Jack.
