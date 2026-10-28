# LV13 - Connection study 2 of 4: the 400 MW offshore wind connection model and four operating cases

## Answer
No. The model is built and all four operating cases converge, but none of them is inside the limits written in advance: every case has at least one exception, 6, 6, 4 and 5 for C1 to C4 [calc: connection-study/results/cases.json]. Each exception has the same computed cause: the two 60 km, 220 kV export circuits generate about 310 MVAr of charging power [calc: connection-study/results/checks.txt], which has to flow through the onshore transformers and the grid impedance and lifts every voltage behind them. The cable ratings, impedances and grid strength are ASSUMED values with no datasheet behind them, so these are findings about an assumed design, not about any real project. One labelled what-if (a 310 MVAr onshore reactor in service in all cases) clears three of four cases and leaves one PCC voltage 0.0021 pu over its limit in C4 [calc: connection-study/results/whatif.txt].

One question was asked and one answered. Study blocks LV14 (cable size, fault levels, grading) and LV15 (N-1, single-line diagram) are not touched here. The branch is `agent/LV13`; nothing is public.

## Model
Single-line, intact network, all circuits in service:

`remote grid (fixed voltage) - Thevenin impedance - 400 kV PCC - 2 x 220/400 kV transformers - 220 kV onshore bus [shunt reactor] - 2 x 60 km 220 kV cables - 220 kV offshore bus - 2 x 66/220 kV transformers - 66 kV bus - 5 strings of 8 turbines (10 MW each)` [calc: connection-study/model/params.py]

Built once as a neutral table (`connection-study/model/build.py`) and read by two solvers: pandapower 3.5.6 [calc: connection-study/results/cases.json] and an independent Newton-Raphson solver copied unchanged from LV12.

## Assumptions
Every input of the model is in this table. DESIGN is the author's choice. ASSUMED is a typical-order value written from general knowledge and NOT SOURCED: a search for cable datasheets found no table with resistance, reactance and capacitance, and the one document that might hold it could not be fetched. No grid code or standard was read for this block.

| ID | Assumption | Value | Unit | Status | Note | Where |
|---|---|---|---|---|---|---|
| A01 | Installed wind capacity | 400.0 | MW | DESIGN | Brief: 400 MW | [calc: connection-study/model/params.py] |
| A02 | Turbines per string | 8 | - | DESIGN | 5 strings x 8 turbines | [calc: connection-study/model/params.py] |
| A03 | Strings | 5 | - | DESIGN | 5 x 8 x 10 MW = 400 MW | [calc: connection-study/model/params.py] |
| A04 | Turbine rating | 10.0 | MW | DESIGN | Generic; no turbine model named | [calc: connection-study/model/params.py] |
| A05 | Turbine transformers (0.69/66 kV) and turbine terminals | omitted | - | DESIGN | Omitted. Each turbine is a constant P and Q injection at the 66 kV array bus. Turbine terminal voltage is therefore not assessed. | [calc: connection-study/model/params.py] |
| A06 | Array cable section lengths: OSS to first turbine / turbine to turbine | 2.5, 1.2 | km | ASSUMED | NOT SOURCED | [calc: connection-study/model/params.py] |
| A07 | Array cable (66 kV, one type for all sections) R / X / C | 0.04, 0.1, 200.0 | ohm/km, ohm/km, nF/km | ASSUMED | Typical order for a 630 mm2 copper 3-core 66 kV cable. NOT SOURCED to a datasheet. | [calc: connection-study/model/params.py] |
| A08 | Array cable provisional continuous rating | 800.0 | A | ASSUMED | PROVISIONAL, NOT SOURCED. Replaced by the cable-sizing block (LV14). | [calc: connection-study/model/params.py] |
| A09 | OSS transformers 66/220 kV: number, rating, impedance voltage, resistive part | 2, 250.0, 14.0, 0.3 | -, MVA each, %, % | ASSUMED | NOT SOURCED. Fixed nominal tap, no-load loss ignored. | [calc: connection-study/model/params.py] |
| A10 | Export cable: circuits, length | 2, 60.0 | -, km | DESIGN | 220 kV three-core AC, brief: 60 km export | [calc: connection-study/model/params.py] |
| A11 | Export cable R / X / C | 0.022, 0.125, 170.0 | ohm/km, ohm/km, nF/km | ASSUMED | Typical order for a ~1000 mm2 copper 220 kV XLPE cable. NOT SOURCED to a datasheet. | [calc: connection-study/model/params.py] |
| A12 | Export cable provisional continuous rating per circuit | 1000.0 | A | ASSUMED | PROVISIONAL, NOT SOURCED. Replaced by LV14. | [calc: connection-study/model/params.py] |
| A13 | Onshore transformers 220/400 kV: number, rating, impedance voltage, resistive part | 2, 250.0, 14.0, 0.3 | -, MVA each, %, % | ASSUMED | NOT SOURCED. Fixed nominal tap. | [calc: connection-study/model/params.py] |
| A14 | Onshore shunt reactor (220 kV), sized as 50 percent of total export cable charging at 220 kV, rounded to 10 MVAr; in service in case C4 only | 160 | MVAr | DESIGN | Value computed in build.py (reactor_mvar). | [calc: connection-study/model/params.py] |
| A15 | Grid at the 400 kV point of connection: short-circuit level, X/R | 10000.0, 10.0 | MVA, - | ASSUMED | NOT SOURCED. Modelled as a Thevenin impedance behind a fixed-voltage remote bus. | [calc: connection-study/model/params.py] |
| A16 | Frequency | 50.0 | Hz | DESIGN |  | [calc: connection-study/model/params.py] |
| A17 | Shunt conductance and cable dielectric loss | omitted | - | DESIGN | Ignored. | [calc: connection-study/model/params.py] |
| A18 | Power factor convention | 0.95 | - | DESIGN | Cases C2 and C3 use 0.95 at the 66 kV array bus. A grid-code reactive requirement was NOT read: NOT SOURCED. | [calc: connection-study/model/params.py] |
| A19 | Reactive limits and OLTC action | omitted | - | DESIGN | None: injections are fixed per case, taps fixed at nominal. | [calc: connection-study/model/params.py] |

## Acceptance criteria
Written and committed before the first run, in their own commit (revision A) [test: connection-study/model/criteria.json]. Summary:

- Voltage: PCC 0.95 to 1.05 pu; every other bus 0.90 to 1.10 pu. Author's design criteria, NOT SOURCED to a standard [test: connection-study/model/criteria.json].
- Loading: cables as current over the provisional rating, transformers as apparent power over nameplate MVA, each at most 100 percent [test: connection-study/model/criteria.json].
- A case is INSIDE LIMITS only if it converges and has no exception. Exceptions are explained by a computed cause; a remedy appears only as a separate labelled what-if, and the base case is never changed after the run [test: connection-study/model/criteria.json].
- Solver to solver: voltage 1e-6 pu, angle 1e-4 degree, flows 1e-4 MW or MVAr, loading 1e-3 percent, energy balance 1e-6 MW, hand check 0.5 percent [test: connection-study/model/criteria.json].

## The four cases and results
Cases (fixed in revision A): C1 rated 400 MW at unity power factor, remote grid 1.00 pu; C2 rated, turbines exporting reactive power at 0.95, remote grid 0.95 pu; C3 rated, turbines absorbing reactive power at 0.95, remote grid 1.05 pu; C4 light wind 40 MW, unity power factor, remote grid 1.05 pu, 160 MVAr reactor in service [test: connection-study/model/criteria.json].

| Case | P gen (MW) | Q gen (MVAr) | P into grid (MW) | Q into grid (MVAr) | Loss (MW) | PCC V (pu) | Max 220 kV V (pu) | Max 66 kV V (pu) | Min 66 kV V (pu) | Array cable (%) | Export cable (%) | OSS trafo (%) | Onshore trafo (%) | Verdict | Source [calc: connection-study/results/cases.json] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 400.0 | 0.0 | 394.70 | 302.00 | 5.30 | 1.0323 | 1.1384 | 1.1451 | 1.1404 | 76.6 | 63.2 | 79.8 | 108.0 | EXCEPTIONS (6) | [calc: connection-study/results/cases.json] |
| C2 | 400.0 | 131.5 | 393.36 | 401.57 | 6.64 | 0.9935 | 1.1402 | 1.1819 | 1.1739 | 79.3 | 74.2 | 85.1 | 126.1 | EXCEPTIONS (6) | [calc: connection-study/results/cases.json] |
| C3 | 400.0 | -131.5 | 395.10 | 182.18 | 4.90 | 1.0700 | 1.1319 | 1.1009 | 1.0998 | 82.8 | 53.4 | 85.5 | 91.5 | EXCEPTIONS (4) | [calc: connection-study/results/cases.json] |
| C4 | 40.0 | 0.0 | 39.23 | 200.21 | 0.77 | 1.0690 | 1.1371 | 1.1429 | 1.1421 | 8.5 | 48.4 | 8.9 | 42.8 | EXCEPTIONS (5) | [calc: connection-study/results/cases.json] |

Powers are in MW and MVAr at the PCC (into the grid). Loss excludes the grid impedance. Voltages are the maximum over the group. Transformer loading is apparent power over nameplate. [calc: connection-study/results/cases.json]

### Exceptions and their cause
- Cause common to all four: charging power. One 60 km circuit at 1.0 pu takes 156.04 MVAr to energise [calc: connection-study/results/checks.txt]; the simple V squared times omega times C times length figure for two circuits is 310.19 MVAr [calc: connection-study/results/checks.txt]. Without a reactor in C1 the PCC exports 302.0 MVAr while the farm exports 394.7 MW [calc: connection-study/results/cases.json].
- First-order check of C1 with the rise equal to reactive power times reactance: 3.020 pu over a grid reactance of 0.00995 pu gives 0.0300 pu, against 0.0323 pu in the model at the PCC; the onshore transformers (0.0280 pu in parallel) give 0.0846 pu, against 0.0891 pu in the model [calc: connection-study/results/checks.txt]. The exceptions are therefore a property of the reactive balance, not a solver artefact.
- C1: 220 kV and 66 kV buses 1.1214 to 1.1451 pu against 1.10; the onshore transformers load to 107.98 percent [calc: connection-study/results/cases.json].
- C2: 66 kV buses reach 1.1819 pu; the onshore transformers load to 126.10 percent because the wind farm adds 131.5 MVAr of exported reactive power to the charging [calc: connection-study/results/cases.json].
- C3: the PCC is 1.0700 pu against 1.05, because the remote grid is already at 1.05 pu and the farm still exports 182.2 MVAr; the 220 kV buses are 1.1319 pu and the 66 kV buses 1.1002 to 1.1009 pu, marginally over 1.10 [calc: connection-study/results/cases.json].
- C4: 40 MW does not change the charging. The PCC is 1.0690 pu with 200.2 MVAr still exported after the 160 MVAr reactor, and all buses are above 1.10 [calc: connection-study/results/cases.json].
- No cable or transformer is overloaded except the two onshore transformers in C1 and C2. Worst cable loading is 82.8 percent (array, C3) and 74.2 percent (export, C2) against provisional ratings [calc: connection-study/results/cases.json].
- Loss at rated output is 4.90 to 6.64 MW, 1.2 to 1.7 percent of 400 MW [calc: connection-study/results/cases.json].

### What-if W1 (not part of the pass rule)
Chosen after the base results were seen, so it is a remedy to be judged, not a result of the study. A 310 MVAr reactor at the 220 kV onshore bus, in service in all four cases, gives: C1 PCC 0.9942 pu, C2 0.9574 pu, C3 1.0290 pu, all inside limits; C4 PCC 1.0521 pu, 0.0021 pu over, with 18.7 MVAr and 39.49 MW exported [calc: connection-study/results/whatif.txt]. Internal voltages in the three full-output cases are 0.9300 to 1.0473 pu and cable loading rises to 98.2 percent in C3 [calc: connection-study/results/whatif.txt]. Reactor sizing, location and switching are open design questions, not settled here.

## Independent check
- A second solver, `connection-study/independent/independent_nr.py`, solves the same data. Worst differences over the four cases: voltage 5.20e-14 pu, angle 1.46e-12 degree, flow 6.86e-11 MW or MVAr, loading 3.61e-11 percent, balance 2.64e-11 MW, all inside the tolerances [calc: connection-study/results/checks.txt].
- Hand check 1: the open-ended circuit reactive power from the pi-circuit input admittance formula is 156.037 MVAr, equal to pandapower to 0.0000 percent [calc: connection-study/results/checks.txt].
- Hand check 2: first array section current in C1, 80 MW over root three times the solved voltage over 800 A, is 76.59 percent against 76.55 percent in the model, a 0.048 percent difference [calc: connection-study/results/checks.txt].
- Sensitivity on the two least certain inputs. Grid short-circuit level 5000 and 20000 MVA against 10000 MVA moves the PCC voltage in C1 to 1.0675 and 1.0158 pu from 1.0323 pu; export cable capacitance of minus and plus 20 percent moves the largest internal voltage in C1 to 1.1092 and 1.1828 pu from 1.1451 pu. No case changes verdict, but at minus 20 percent capacitance C1 falls from 6 exceptions to 3 and C3 from 4 to 1, so the verdict count is sensitive to the cable data [calc: connection-study/results/sensitivity.txt].
- Tests: 6 passed, run from a clean shell with `python3 -m pytest -q` in `connection-study/` [test: connection-study/tests/test_lv13.py].

## Findings
- pandapower's `loading_percent` for a transformer is current over rated current. At 1.14 pu it reads 96.29 percent for the onshore transformers in C1 where apparent power over nameplate is 107.98 percent [calc: connection-study/results/cases.json]. The criteria use apparent power, so the higher figure is the one reported. Anyone quoting pandapower's transformer loading above 1 pu reads it low.
- The model's cable charging is large because two 60 km circuits at 220 kV are modelled with no compensation at either end; the capacitance (170 nF/km) is ASSUMED [calc: connection-study/model/params.py].
- The 66 kV array voltage is only 0.0017 to 0.0047 pu above the OSS bus in C1, so the array voltage follows the export system, not the string length [calc: connection-study/results/cases.json].

## Hand check for Jack (the approval step)
Compute V squared times omega times C times length for one export circuit: 220 squared times 2 pi 50 times 170e-9 times 60 gives 155.09 MVAr. The pi-circuit formula in `connection-study/model/checks.py` function `open_line_q` gives 156.037 MVAr, and pandapower gives the same [calc: connection-study/results/checks.txt]. Then defend the ASSUMED rows aloud, especially A11, A12 and A15.

## Decisions for Jack
- Sunday: this ran on Sunday 18 October 2026 on Jack's explicit instruction in the session, overriding the rest day for this block only.
- Are the base-case exceptions acceptable as the study's finding, or should revision B put a compensation scheme into the base design (a new criteria revision, with the reason written down)?
- Replace the NOT SOURCED cable and transformer values with datasheet values when Jack can supply them in `inputs/LV13/`.
- Make the repository public yourself when satisfied. I did not.

## Sources
- No external source is cited for any value. Typical-order values are ASSUMED and NOT SOURCED. A search found the ABB submarine cable guide (tethys.pnnl.gov, ABB_et_al_2019.pdf) but it could not be fetched, so nothing from it is used.
- Independent solver and MATPOWER-format reader copied unchanged from LV12 [test: connection-study/independent/independent_nr.py].

## Other questions this raised, not answered here
- What reactive compensation (size, location, switching) does a 60 km, 220 kV, two-circuit export need? Belongs to a revision B or LV14. [calc: connection-study/model/params.py]
- What do the Grid Code and the security standard require of voltage and reactive range at 400 kV? Not read: NOT SOURCED.

## Limits
- Self-directed study on assumed data. It is not professional experience and has not been reviewed by a chartered engineer.
- Turbine transformers, taps, dielectric loss and reactive limits are omitted (A05, A17, A19).
- The cable ratings are provisional and replaced by LV14.

## Gate
- Kind: calc
- Prepared: Claude Code (lev-portfolio), 18 October 2026, criteria first in commit 0b0e0f9
- Checked: second solver and hand formulae, `connection-study/results/checks.txt`, and `python3 -m pytest -q` (6 passed); no second agent has reviewed it
- Approved: pending Jack
