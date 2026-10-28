"""Every assumption of the LV13 model, in one place. The assumptions table is generated from ASSUMPTIONS.

Status words: DESIGN = a choice of the author; ASSUMED = a typical-order value written from general
knowledge, NOT SOURCED to a datasheet or standard (no datasheet was reachable in the build session).
Nothing here is professional data. Self-directed study on assumed data.
"""
import math

F_HZ = 50.0
BASE_MVA = 100.0

# ID: (description, value, unit, status, note)
ASSUMPTIONS = {
    "A01": ("Installed wind capacity", 400.0, "MW", "DESIGN", "Brief: 400 MW"),
    "A02": ("Turbines per string", 8, "-", "DESIGN", "5 strings x 8 turbines"),
    "A03": ("Strings", 5, "-", "DESIGN", "5 x 8 x 10 MW = 400 MW"),
    "A04": ("Turbine rating", 10.0, "MW", "DESIGN", "Generic; no turbine model named"),
    "A05": ("Turbine transformers (0.69/66 kV) and turbine terminals", None, "-", "DESIGN", "Omitted. Each turbine is a constant P and Q injection at the 66 kV array bus. Turbine terminal voltage is therefore not assessed."),
    "A06": ("Array cable section lengths: OSS to first turbine / turbine to turbine", (2.5, 1.2), "km", "ASSUMED", "NOT SOURCED"),
    "A07": ("Array cable (66 kV, one type for all sections) R / X / C", (0.040, 0.100, 200.0), "ohm/km, ohm/km, nF/km", "ASSUMED", "Typical order for a 630 mm2 copper 3-core 66 kV cable. NOT SOURCED to a datasheet."),
    "A08": ("Array cable provisional continuous rating", 800.0, "A", "ASSUMED", "PROVISIONAL, NOT SOURCED. Replaced by the cable-sizing block (LV14)."),
    "A09": ("OSS transformers 66/220 kV: number, rating, impedance voltage, resistive part", (2, 250.0, 14.0, 0.30), "-, MVA each, %, %", "ASSUMED", "NOT SOURCED. Fixed nominal tap, no-load loss ignored."),
    "A10": ("Export cable: circuits, length", (2, 60.0), "-, km", "DESIGN", "220 kV three-core AC, brief: 60 km export"),
    "A11": ("Export cable R / X / C", (0.022, 0.125, 170.0), "ohm/km, ohm/km, nF/km", "ASSUMED", "Typical order for a ~1000 mm2 copper 220 kV XLPE cable. NOT SOURCED to a datasheet."),
    "A12": ("Export cable provisional continuous rating per circuit", 1000.0, "A", "ASSUMED", "PROVISIONAL, NOT SOURCED. Replaced by LV14."),
    "A13": ("Onshore transformers 220/400 kV: number, rating, impedance voltage, resistive part", (2, 250.0, 14.0, 0.30), "-, MVA each, %, %", "ASSUMED", "NOT SOURCED. Fixed nominal tap."),
    "A14": ("Onshore shunt reactor (220 kV), sized as 50 percent of total export cable charging at 220 kV, rounded to 10 MVAr; in service in case C4 only", "computed", "MVAr", "DESIGN", "Value computed in build.py (reactor_mvar)."),
    "A15": ("Grid at the 400 kV point of connection: short-circuit level, X/R", (10000.0, 10.0), "MVA, -", "ASSUMED", "NOT SOURCED. Modelled as a Thevenin impedance behind a fixed-voltage remote bus."),
    "A16": ("Frequency", F_HZ, "Hz", "DESIGN", ""),
    "A17": ("Shunt conductance and cable dielectric loss", None, "-", "DESIGN", "Ignored."),
    "A18": ("Power factor convention", 0.95, "-", "DESIGN", "Cases C2 and C3 use 0.95 at the 66 kV array bus. A grid-code reactive requirement was NOT read: NOT SOURCED."),
    "A19": ("Reactive limits and OLTC action", None, "-", "DESIGN", "None: injections are fixed per case, taps fixed at nominal."),
}

N_STRINGS = ASSUMPTIONS["A03"][1]
N_TURB = ASSUMPTIONS["A02"][1]
P_TURB = ASSUMPTIONS["A04"][1]
LEN_FIRST, LEN_STEP = ASSUMPTIONS["A06"][1]
ARR_R, ARR_X, ARR_C = ASSUMPTIONS["A07"][1]
ARR_IMAX_KA = ASSUMPTIONS["A08"][1] / 1000
N_TR_OSS, S_TR_OSS, UK_OSS, UR_OSS = ASSUMPTIONS["A09"][1]
N_EXP, LEN_EXP = ASSUMPTIONS["A10"][1]
EXP_R, EXP_X, EXP_C = ASSUMPTIONS["A11"][1]
EXP_IMAX_KA = ASSUMPTIONS["A12"][1] / 1000
N_TR_ON, S_TR_ON, UK_ON, UR_ON = ASSUMPTIONS["A13"][1]
SCL_MVA, GRID_XR = ASSUMPTIONS["A15"][1]


def reactor_mvar(exp_c_nf=EXP_C):
    """Half of the total export cable charging at nominal 220 kV, to the nearest 10 MVAr."""
    qc = N_EXP * 220.0 ** 2 * 2 * math.pi * F_HZ * exp_c_nf * 1e-9 * LEN_EXP
    return round(0.5 * qc, -1)
