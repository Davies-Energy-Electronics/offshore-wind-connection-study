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
