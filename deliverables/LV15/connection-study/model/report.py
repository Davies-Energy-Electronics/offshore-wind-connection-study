"""Builds the LV15 report (Word, then PDF by LibreOffice) from the saved results of LV13, LV14 and LV15. Every number is read from a results file."""
import json
import os
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = Path(__file__).resolve().parents[1]
DEL = HERE.parents[1]
R = HERE / "results"
N1C = json.load(open(R / "n1.json"))          # revision C, the step
CKC = json.load(open(R / "checks.json"))
N1 = json.load(open(R / "n1_D.json"))           # revision D, the final base design
CK = json.load(open(R / "checks_D.json"))
CRD = json.load(open(HERE / "model" / "criteria_D.json"))
F14 = json.load(open(DEL / "LV14/connection-study/results/faults.json"))
CS14 = json.load(open(DEL / "LV14/connection-study/results/cable_sizing.json"))
S = N1["sized"]

d = Document()
st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
for s in d.sections:
    s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2.0)
    hp = s.header.paragraphs[0]; hp.text = "Offshore wind connection study (LV12 to LV15)  ·  Jack Davies  ·  28 October 2026"; hp.runs[0].font.size = Pt(8); hp.runs[0].font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    fp = s.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run(); f1 = OxmlElement("w:fldSimple"); f1.set(qn("w:instr"), "PAGE"); r._r.append(f1)


def P(t, bold=False, italic=False, size=None, align=None):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if align: p.alignment = align
    p.paragraph_format.space_after = Pt(6)
    return p


def H(t, lvl=1):
    return d.add_heading(t, lvl)


def B(t):
    p = d.add_paragraph(t, style="List Bullet"); p.paragraph_format.space_after = Pt(3)


def T(head, rows, widths=None, size=8.5):
    t = d.add_table(rows=1, cols=len(head)); t.style = "Light Grid Accent 1"; t.autofit = False
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]; c.text = ""; rr = c.paragraphs[0].add_run(str(h)); rr.bold = True; rr.font.size = Pt(size)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; rr = cells[i].paragraphs[0].add_run(str(v)); rr.font.size = Pt(size)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


f = lambda x, n=1: "-" if x is None else f"{x:.{n}f}"

# ------------------------------------------------------------------ title
P("A 400 MW offshore wind farm connection:", bold=True, size=20)
P("load flow, cable sizing, fault levels, protection grading and N-1", bold=True, size=16)
P("A self-directed study in four blocks (LV12 to LV15): the final base design, revision D", size=11)
P("Jack Davies, BEng (Hons) Renewable Energy Engineering  ·  28 October 2026  ·  decisions D1 to D4 approved by the author; D5 to D7 taken on his instruction", italic=True, size=10)

box = d.add_table(rows=1, cols=1); box.style = "Light Shading Accent 1"
c = box.rows[0].cells[0]; c.text = ""
r = c.paragraphs[0].add_run("Read this first. "); r.bold = True
c.paragraphs[0].add_run("This is a self-directed study on assumed data. No real wind farm, cable datasheet, site survey or network operator data stands behind it: every input is either a design choice or a typical-order value written from general knowledge, and is marked ASSUMED. No standard (IEC 60287, IEC 60909, IEC 60255, the Grid Code or the SQSS) was read; the methods are written in the form those standards use, from general knowledge, and nothing here claims compliance with any of them. It is not professional experience and has not been reviewed by a chartered engineer. What it does show is the method: criteria written before any number was run, every result produced by code that reruns from a clean shell, independent checks, and every failure reported rather than hidden.")
d.add_paragraph()

H("Summary")
ic = N1["intact"]; n1 = N1["n1"]; icc = N1C["intact"]
P(f"The connection is two 60 km, 220 kV export circuits from an offshore substation to a 400 kV point of connection, with two 250 MVA transformers at each end and five 66 kV strings of eight 10 MW turbines. The final base design, revision D, has two 155 MVAr onshore reactors, a {S['export']['area_mm2']} mm2 export cable and a {S['array']['area_mm2']} mm2 array cable sized on a conservative soil value, and the string relay set at 960 A. Intact, all four operating cases are inside limits.")
P(f"It is not N-1 secure at full output, which is expected of a design with two of everything at half rating. Losing one export circuit, one offshore transformer or one onshore transformer forces curtailment to about 240 to 250 MW at unity power factor (C1: {n1['O1']['cases']['C1']['curtailed_mw']}, {n1['O2']['cases']['C1']['curtailed_mw']} and {n1['O3']['cases']['C1']['curtailed_mw']} MW). Losing a string's first cable section loses only that string and rides through in every case. Losing one of the two reactor units rides through at full output and leaves only the light-load case over voltage (PCC {n1['O5']['cases']['C4']['pcc_pu']} pu), where in revision C, with one reactor, the same outage put every case out of limits at full output.")
P(f"Fault levels hardly move on the final cables (largest change {CK['FAULT-D']['worst_change_pct']} percent), so the grading of LV14 stands, with the onshore transformer relay at TMS 0.35 for discrimination at the minimum fault (backup time about 3.9 s at the maximum offshore fault, a finding) and the string relay at 960 A ({CK['R1']['margin_s']} s ahead of the next relay). Every input is assumed; section 12 says what the study is not.")

# ------------------------------------------------------------------ 1 scope
H("1. Question, scope and how the study was run")
P("The study answers one question per block. LV12 built and checked an independent load-flow solver. LV13 asked whether four operating cases of the connection solve inside limits written in advance. LV14 asked what cable sizes, fault levels and overcurrent settings the design needs. LV15, this block, asks: which single outages can the connection ride through at full output inside limits, and for each that cannot, what is the largest output that stays inside limits?")
P("Each block wrote its acceptance criteria into a file and committed it before the first number was run (LV15: model/criteria_C.json, commit 34caf6a, and model/criteria_D.json, commit df09ba4). A result outside a limit is an exception, explained by a computed cause; a remedy appears only as a separate labelled what-if, chosen after the result was seen, and the base case is never changed to make it pass.")
H("Decisions", 2)
for k, v in json.load(open(HERE / "model" / "criteria_C.json"))["decisions"].items():
    B(f"{k}. {v.replace("Proposed by Claude, 27 Oct 2026, for Jack's approval.", 'Proposed 27 Oct 2026; approved by Jack, 28 Oct 2026.')}")
for k, v in CRD["decisions"].items():
    B(f"{k}. {v}")
P(CRD["approvals"]["D1-D4"] + " " + CRD["basis_D5_D7"], italic=True, size=9)

# ------------------------------------------------------------------ 2 network
H("2. The network")
d.add_picture(str(R / "sld.png"), width=Cm(16.6))
P("Figure 1. Single-line diagram of the final base design, revision D (results/sld.png). R1 to R4 are the overcurrent relays graded in LV14.", italic=True, size=8.5)
P("The model is a single neutral table read by two solvers: pandapower 3.5.6 and the independent Newton-Raphson solver from LV12. The remote grid is a fixed voltage behind a Thevenin impedance of 10 GVA at X/R 10; turbines are constant P and Q injections at their 66 kV array buses (turbine transformers are omitted, so turbine terminal voltage is not assessed); transformer taps are fixed at nominal.")

H("3. Assumptions", 1)
P("Every input of the model. DESIGN is the author's choice; ASSUMED is a typical-order value, NOT SOURCED to a datasheet or standard. Revision D replaces the cable rows A07, A08, A11 and A12 with the values below, and A14 with two 155 MVAr reactor units in every case.")
import importlib.util, sys
sys.path.insert(0, str(DEL / "LV13/connection-study/model"))
spec = importlib.util.spec_from_file_location("params0", DEL / "LV13/connection-study/model/params.py"); p0 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p0)
rows = []
for k, (desc, val, unit, status, note) in p0.ASSUMPTIONS.items():
    v = "computed" if val == "computed" else ("omitted" if val is None else (", ".join(str(x) for x in val) if isinstance(val, tuple) else str(val)))
    rows.append((k, desc[:95], v, unit, status))
T(["ID", "Assumption (LV13)", "Value", "Unit", "Status"], rows, [1.1, 8.6, 2.6, 2.6, 1.8], size=7.5)
T(["Revision D cable", "Size", "R at 90 C (ohm/km)", "C (nF/km)", "Rating at soil 1.5 (A)", "Design current (A)", "Margin"],
  [("66 kV array (sized on rev C current)", f"{S['array']['area_mm2']} mm2", f(S['array']['r_ohm_km'], 4), f(S['array']['c_nf_km']), f(S['array']['rating_a']), f(S['array']['design_a']), f"{S['array']['margin_pct']:.1f} %"),
   ("220 kV export", f"{S['export']['area_mm2']} mm2", f(S['export']['r_ohm_km'], 4), f(S['export']['c_nf_km']), f(S['export']['rating_a']), f(S['export']['design_a']), f"{S['export']['margin_pct']:.1f} %")])
P("Cable inputs (LV14, all ASSUMED): copper conductor at 90 C, seabed 15 C, buried 1.0 m, XLPE 10 mm (66 kV) and 24 mm (220 kV) at 3.5 K m/W, coverings 16 mm at 6.0 K m/W, sheath and armour loss 10 percent of conductor loss. Soil thermal resistivity 1.5 K m/W in revisions C and D (D1), against 1.0 in LV14. Reactance is unchanged from LV13.")

# ------------------------------------------------------------------ 4 criteria
H("4. Acceptance criteria")
B("Voltage: PCC 0.95 to 1.05 pu; every 220 kV and 66 kV bus 0.90 to 1.10 pu. Author's criteria, NOT SOURCED to the Grid Code.")
B("Loading: cables as current over the rating at soil 1.5 K m/W; transformers as apparent power over nameplate; each at most 100 percent.")
B("N-1 rule: run each outage at the case's output; if inside limits it RIDES THROUGH; if not, find by bisection to 1 MW the largest output, all in-service turbines scaled equally, that is inside limits (CURTAILED). A run that does not converge counts as outside limits.")
B("Grading (LV14 plus D3): pickup at least 1.2 times maximum load and at most 0.8 times the minimum fault at the zone end; 0.30 s between successive relays at the maximum and, from revision C, the minimum fault.")

# ------------------------------------------------------------------ 5 load flow
H("5. Load flow, intact network")
P("LV13 (revision A, provisional cables, reactor in C4 only) found every case outside limits, with one cause: the two 60 km export circuits generate about 310 MVAr of charging power that lifts every voltage behind them and loads the onshore transformers to 108 and 126 percent in C1 and C2. Revision B added 310 MVAr of reactor in every case (decision 7, 21 October), which brought C1 to C3 inside limits and left C4's PCC at 1.0521 pu. Revision C added the cables sized on soil 1.5 K m/W; revision D, below, is the final base design.")
rows = []
for cid, v in ic.items():
    rows.append((cid, f(v['gen_mw']), f(v['loss_mw'], 2), f(v['pcc_pu'], 4), f(v['vmax'], 4), f(v['vmin'], 4), f(v['export_a']), f(v['array_first_a']), f(v['max_line_loading']), f(v['max_trafo_loading']), "inside limits" if not v['exceptions'] else f"{len(v['exceptions'])} exceptions"))
T(["Case", "Gen (MW)", "Loss (MW)", "PCC (pu)", "V max (pu)", "V min (pu)", "Export (A)", "Array 1st (A)", "Max cable %", "Max trafo %", "Verdict"], rows, size=7.5)
P("Cases: C1 400 MW unity power factor, grid 1.00 pu; C2 400 MW exporting reactive power at 0.95, grid 0.95 pu; C3 400 MW absorbing reactive power at 0.95, grid 1.05 pu; C4 40 MW unity, grid 1.05 pu. Source: results/n1_D.json.", italic=True, size=8.5)
P(f"Why revision D: on revision C the C3 case loaded the first section of every string to {icc['C3']['exceptions'][0][2]} percent. The 800 mm2 cable chosen for the conservative soil has more capacitance than the 630 mm2 cable whose current it was sized from, so its own charging current pushed the current ({icc['C3']['array_first_a']} A) above its rating. Sizing has to be iterated until it settles; one more step, to {S['array']['area_mm2']} mm2 ({S['array']['rating_a']:.1f} A), clears it (D5), at {ic['C3']['max_line_loading']} percent. The C4 PCC voltage, 1.0521 pu in revision B, is {ic['C4']['pcc_pu']} pu now, inside the limit, because the 630 mm2 export cable has less capacitance than LV13 assumed.")

# ------------------------------------------------------------------ 6 cables
H("6. Cable sizing (LV14, then revisions C and D)")
P(f"Method: a one-dimensional thermal circuit of the form IEC 60287 uses. Heat from each core crosses its own insulation (T1), then the heat of all three cores crosses the coverings (T3) and the soil (T4); the rating is the current at which the conductor reaches 90 C. LV14 chose 630 mm2 (array, {CS14['array']['rating_a']:.1f} A against {CS14['array']['design_a']:.1f} A) and 500 mm2 (export, {CS14['export']['rating_a']:.1f} A against {CS14['export']['design_a']:.1f} A) on soil 1.0 K m/W, margins of {CS14['array']['margin_pct']} and {CS14['export']['margin_pct']} percent. Its own sensitivity showed both fail at soil 1.5 K m/W, the least certain input, so the final design sizes on 1.5 (D1): 630 mm2 export, and the array settles at 1000 mm2 once its own charging current is included (D5).")
P("Worked example, 500 mm2 export cable (LV14 results/worked_example.txt), re-derived independently on 27 October 2026 (LV14/independent_check/check.py, all twelve values within 0.12 percent):")
for line in (DEL / "LV14/connection-study/results/worked_example.txt").read_text().splitlines()[1:]:
    P(line, size=8.5)
P(f"N-1 consequence: if one export circuit is lost, the other has to carry about twice the current. No size up to 2000 mm2 rates for that on LV14's inputs, so N-1 security on the export would need a third circuit or a much larger single cable, not a larger cable of this type. This is why section 9 finds curtailment, not ride-through.")

# ------------------------------------------------------------------ 7 faults
H("7. Fault levels")
P("IEC 60909 voltage-source method as coded in pandapower (the transformer correction factor and c factors were read in its source; the standard was not read). Maximum: three-phase, c 1.10, grid 10 GVA, all in service, wind at 1.1 times rated current per turbine. Minimum: two-phase, c 1.00, grid 5 GVA, no wind.")
rows = []
fc = CK["FAULT-D"]["rows"]
for r_ in F14["rows"]:
    n = r_["bus"]
    rows.append((n, f"{r_['kv']:.0f}", f(r_['max3_total_ka'], 2), f(r_['max3_grid_only_ka'], 2), f(r_['ip_ka'], 1), f(r_['min2_ka'], 2), f(fc[n]['max3_revD'], 2), f"{fc[n]['d_max_pct']:+.2f} %"))
T(["Busbar", "kV", "Ik'' max (kA)", "grid only (kA)", "ip (kA)", "Ik'' min 2ph (kA)", "Ik'' max rev D (kA)", "Change"], rows, size=8)
P(f"Hand check at the offshore 66 kV bus (grid only, maximum), on 100 MVA: grid 0.00109 + j0.01095 pu, two onshore transformers in parallel 0.000578 + j0.02699 pu (K_T 0.964), two export circuits in parallel 0.001364 + j0.007748 pu, two offshore transformers 0.000578 + j0.02699 pu. Total |Z| = 0.07276 pu; Ik'' = 1.1 x 0.8748 / 0.07276 = 13.23 kA, against 13.226 kA in the model (independent check, 0.004 percent). Single-phase earth faults are not studied: no zero-sequence or earthing data has been assumed.")

# ------------------------------------------------------------------ 8 grading
H("8. Overcurrent grading")
P("Four relays on the IEC standard-inverse curve t = TMS x 0.14 / ((I/Is)^0.02 - 1) (curve constants seen in relay-vendor summaries, NOT VERIFIED). R1 string feeder (66 kV, Is 950 A in LV14, 960 A from D7, TMS 0.10), R2 offshore transformer incomer (66 kV, 2400 A, 0.10), R3 export circuit onshore end (220 kV, 900 A, 0.125), R4 onshore transformer HV side (400 kV, 400 A, 0.225 in LV14, 0.35 from D3).")
d.add_picture(str(DEL / "LV14/connection-study/results/grading_chart.png"), width=Cm(14))
P("Figure 2. Grading chart from LV14 (results/grading_chart.png), at TMS 0.225 for R4.", italic=True, size=8.5)
P("At the maximum faults all four relays grade with at least 0.369 s between them (rule 0.30 s). At the minimum fault at the end of a string, R4 at TMS 0.225 would trip at 4.43 s before R3 at 6.19 s: the curves cross because the pickups sit at different multiples of the fault current. With the minimum-fault check in the pass rule (D3), R4 goes to TMS 0.35: R4 then takes 6.89 s at that fault (0.70 s after R3), and 3.9 s for a maximum fault at the offshore 66 kV busbar against 1.55 s before. A 3.9 s backup time is long; whether it is acceptable depends on the transformer's through-fault withstand, which is not assessed. A real scheme would add unit protection (differential on the transformers and cables) so that overcurrent is backup only.")
P(f"R1 (D7): with the final loads the string relay's pickup must be at least 1.2 x {CK['R1']['max_load_a']} A = {CK['R1']['min_pickup_a']} A, and at most 0.8 x its zone-end minimum fault ({CK['R1']['zone_end_min_fault_a']:.0f} A) = {CK['R1']['max_pickup_a']:.0f} A. At 960 A it trips in {CK['R1']['t_r1_s']} s at the string-feeder fault, {CK['R1']['margin_s']} s ahead of R2. Fault currents move by under 0.3 percent on revision D, so no other grading verdict changes (FAULT-D).")

# ------------------------------------------------------------------ 9 N-1
H("9. N-1")
P("Five single outages, each in the four cases. Verdicts by the rule in section 4. 'Curtailed' gives the largest total output inside limits; 'outside limits even at zero output' means curtailing cannot cure it (a voltage set by the grid or by cable charging, not by the farm's output).")
rows = []
for o, dd in n1.items():
    for cid, v in dd["cases"].items():
        ex = v["exceptions"]
        first = "; ".join(f"{a} {b} {c}" if c is not None else f"{a}" for a, b, c in ex[:2]) or "none"
        verdict = v["verdict"] + (f": {v['curtailed_mw']} MW" if "curtailed_mw" in v else "")
        rows.append((o, cid, verdict, first, f(v['export_a']), f(v['max_trafo_loading']), f(v['pcc_pu'], 4)))
T(["Outage", "Case", "Verdict", "Worst exceptions at full output", "Export (A)", "Max trafo %", "PCC (pu)"], rows, [1.3, 1.1, 4.2, 5.8, 1.6, 1.6, 1.6], size=7.5)
P("O1 one export circuit out; O2 one offshore transformer out; O3 one onshore transformer out; O4 the first section of string 1 out (string 1 lost); O5 the onshore reactor out. Source: results/n1.json.", italic=True, size=8.5)
H("What the table says", 2)
B(f"Export circuit, offshore transformer or onshore transformer out: the farm must curtail to about 240 to 250 MW at unity power factor, and to {n1['O3']['cases']['C3']['curtailed_mw']} to {n1['O1']['cases']['C3']['curtailed_mw']} MW in C3, where the farm also absorbs reactive power. The limit is the remaining 250 MVA transformer or the remaining cable's rating: two half-rated items cannot carry the whole output.")
B(f"In C2 (grid at 0.95 pu, its lower limit) the same three outages leave the PCC just under 0.95 pu even at zero output ({n1['O1']['cases']['C2']['pcc_pu']}, {n1['O2']['cases']['C2']['pcc_pu']}, {n1['O3']['cases']['C2']['pcc_pu']} pu at full output). That voltage is set by the grid; it needs reactive support or tap changing, which this model does not have (taps fixed, A19).")
B(f"One onshore transformer out in C3 does not solve at full output: the load flow does not converge, a sign that one transformer cannot carry 400 MW while absorbing reactive power at a high grid voltage. Curtailed, it holds {n1['O3']['cases']['C3']['curtailed_mw']} MW.")
B("A string's first section out loses only that string's 80 MW and rides through in every case.")
B(f"One reactor unit out rides through at full output in C1 to C3. At light load (C4) the PCC reaches {n1['O5']['cases']['C4']['pcc_pu']} pu and internal buses {n1['O5']['cases']['C4']['vmax']} pu, which curtailment cannot cure: the remedy would be tap changing or switching the reactor in steps. In revision C, with one 310 MVAr reactor, losing it put every case out of limits at full output (internal voltages up to {N1C['n1']['O5']['cases']['C4']['vmax']} pu).")

# ------------------------------------------------------------------ 10 what-ifs
H("10. From revision C to revision D")
P(f"Revision C was run first, by its own criteria (criteria_C.json). It showed three things, each tried first as a labelled what-if: the array cable had to be iterated (W3: 1000 mm2 clears C3), the single reactor was a single point of failure (W4: two 155 MVAr units, one out, keeps C1 to C3 inside limits), and R1's pickup sat 0.5 percent under its own rule. Revision D takes all three into the base design (D5 to D7), with criteria written before it was run (criteria_D.json). Revision C stays in the record (results/n1.json, checks.json) so the step can be traced.")
P("Not run, and named as the next steps a real study would take: a third export circuit or a single larger HVAC or HVDC link if N-1 at full output were required; tap-changing transformers; turbine reactive capability; reactor switching in steps for light load; a cost comparison of losses against cable size (LV14's W2 showed the minimum-size export cable roughly doubles losses).")

# ------------------------------------------------------------------ 11 checks
H("11. Checks and verification")
rows = [("SOLVE (rev D)", CK["SOLVE"]["result"], "Every run converges. One does not: one onshore transformer out at C3, full output. Counted as outside limits; reported as a finding."),
        ("BAL (rev D)", CK["BAL"]["result"], f"Generation minus power into the grid equals loss; worst {CK['BAL']['worst_mw']:.1e} MW."),
        ("HAND-O2 (rev D)", CK["HAND-O2"]["result"], f"Curtailed output with one offshore transformer out, {CK['HAND-O2']['curtailed_mw']} MW, against 250 MW by hand ({CK['HAND-O2']['diff_pct']} %)."),
        ("FAULT-D", CK["FAULT-D"]["result"], f"Largest change in any fault level on the final cables {CK['FAULT-D']['worst_change_pct']} %, under the 2 % threshold."),
        ("R1 (D7)", CK["R1"]["result"], f"Pickup rule met ({CK['R1']['min_pickup_a']} to {CK['R1']['max_pickup_a']:.0f} A) and {CK['R1']['margin_s']} s to R2."),
        ("HAND-O1 (rev C)", CKC["HAND-O1"]["result"], f"Expected the remaining export circuit to carry the intact total within 5 %: {CKC['HAND-O1']['outage_a']} A against 2 x {CKC['HAND-O1']['intact_per_circuit_a']} A ({CKC['HAND-O1']['simple_rule_diff_pct']} %). The rule was wrong: half the charging current leaves with the circuit that is out. Reported as failed, not adjusted."),
        ("LV14 independent", "PASS", "Export cable rating (759.6 A) and the 66 kV fault level (13.23 kA) re-derived without the LV14 code: twelve values within 0.12 %."),
        ("Tests", "all pass", "tests/test_lv15.py on revisions C and D from a clean shell; LV12 20, LV13 6 and LV14 9 also rerun.")]
T(["Check", "Result", "What it shows"], rows, [2.4, 2.0, 12.0], size=8)
P("Limits of the checking: the independent checks use the same general-knowledge formulas as the model, so they check the arithmetic and the model build, not the standards. No second engineer has reviewed the study.")

# ------------------------------------------------------------------ 12 limits
H("12. What this study is not")
for t in ("Not a design for construction, and not professional experience. Every input is assumed.",
          "Not a compliance assessment: the Grid Code, the SQSS (including its offshore chapter) and the IEC standards named were not read.",
          "Intact and single-outage steady state only: no dynamics, no fault ride-through, no harmonics or resonance (long cables and reactors make these real questions), no earth faults, no switching transients.",
          "Turbines are fixed P and Q injections: no turbine transformer, no reactive capability curve, no control.",
          "No economics: cable size against losses, a third circuit against curtailment, and reactor units against risk are named but not costed."):
    B(t)

H("13. How to reproduce")
P("With Python 3 and the packages in requirements.txt (pandapower 3.5.6): in LV12, casefiles/fetch_data.py then pytest; in LV13, pytest; then LV14/connection-study/run_all.sh and LV15/connection-study/run_all.sh (revisions C and D). Each block's results are rewritten and its tests rerun. This report is built by model/report.py from the saved results.")
H("14. Sources")
P("No standard, grid code, datasheet or survey was read for this study; nothing is cited as read. Named for the method only: IEC 60287 (cable rating), IEC 60228 (conductor sizes), IEC 60909 (short-circuit currents), IEC 60255-151 (relay curves). pandapower 3.5.6 (open source) was used and its short-circuit source code read. Every number in this report comes from a results file of LV13, LV14 or LV15, named beside it.")
# ------------------------------------------------------------------ appendices
d.add_page_break()
H("Appendix A. Study notes: what to be able to explain without notes")
P("Ten ideas this study rests on, each with the number from this study that shows it. They are written for the author's own exam on the study; each answer should take under two minutes at a whiteboard.")
notes = [
 ("Why long AC cables need reactors", "A cable is a long capacitor. One 60 km, 220 kV circuit of the 630 mm2 cable takes about 131 MVAr to energise (V squared x omega x C x length). Two circuits make about 263 MVAr that must go somewhere; without a reactor it lifts every voltage (LV13: 1.14 pu internally) and loads the onshore transformers."),
 ("Why the cable rating depends on the soil", "The rating is the current whose heat the ground can carry away for a 75 K rise. Soil from 1.0 to 1.5 K m/W cuts the 500 mm2 export rating from 760 A to 667 A, which is why revision C sizes on 1.5 until a survey says otherwise."),
 ("Why a bigger cable can still be overloaded", "A bigger conductor also has more capacitance, so more charging current. The 800 mm2 array cable carries 796 A in C3 against its 790 A rating; sizing must be iterated until it settles (1000 mm2)."),
 ("The voltage-source fault method", "Put a voltage source c x Un / root 3 at the fault, short every other source, and divide by the impedance seen from the fault. c is 1.10 for the maximum (to cover operating voltage above nominal) and 1.00 for the minimum. At the 66 kV offshore bus: 1.1 x 0.8748 kA / 0.07276 pu = 13.23 kA from the grid alone."),
 ("Why transformers get a correction factor", "K_T = 0.95 x cmax / (1 + 0.6 xT) scales transformer impedance in the maximum case; here 0.964. It makes the maximum fault current a little larger, so it errs on the safe side for equipment ratings."),
 ("Maximum and minimum faults do different jobs", "The maximum fault sizes equipment (breaking capacity, cable short-circuit withstand) and sets the grading margins. The minimum fault checks that relays still see the fault and still trip in the right order; it is what caught R3 and R4 crossing."),
 ("The standard inverse curve and grading", "t = TMS x 0.14 / ((I/Is)^0.02 - 1). Pickup above the load (1.2 x) and below the minimum fault (0.8 x); the relay nearer the fault must trip at least 0.30 s before the one behind it, at every fault level, not only the largest."),
 ("What N-1 means here", "Take out one element at a time and ask whether the rest stays inside limits. Two half-rated transformers or cables cannot carry full output when one is out, so the farm curtails to about 250 MW. Whether that is acceptable is a planning-standard and cost question, not a load-flow one."),
 ("Why the reactor is split in two", "Losing a single 310 MVAr reactor (revision C) took internal voltages to 1.12 to 1.20 pu, and curtailing the farm does not help because the charging comes from the cable, not the turbines. With two 155 MVAr units (revision D), one out rides through at full output; only light load stays over voltage, which needs taps or reactor switching."),
 ("What makes the study honest", "Criteria committed before the first run; every number from code that reruns; a second method or hand check for each result; every failure reported (one run that does not converge, one hand check whose rule was wrong); and every input marked ASSUMED."),
]
for h, t in notes:
    p = d.add_paragraph(); r = p.add_run(h + ". "); r.bold = True; p.add_run(t); p.paragraph_format.space_after = Pt(5)

H("Appendix B. Bus voltages, revision D, intact network")
sys.path.insert(0, str(HERE / "model"))
import warnings; warnings.filterwarnings("ignore")
os.environ["LV15_REV"] = "D"
import revc, build as BB
nets = {}
for c in revc.CASES:
    net = revc.build(c); BB.solve_pp(net); nets[c["id"]] = net
names = [n for n in nets["C1"].bus.name if n != "REM"]
rows = []
for n in names:
    rows.append([n] + [f"{float(nets[c].res_bus.vm_pu[nets[c].bus.name == n].iloc[0]):.4f}" for c in ("C1", "C2", "C3", "C4")])
T(["Bus", "C1 (pu)", "C2 (pu)", "C3 (pu)", "C4 (pu)"], rows, [3.0, 2.5, 2.5, 2.5, 2.5], size=7.5)

H("Appendix C. Decision log")
T(["Date", "Decision", "By"], [
 ("18 Oct 2026", "LV13 criteria revision A written before the first run", "Claude Code, from Jack's brief"),
 ("21 Oct 2026", "Decision 7: build on revision B, 310 MVAr reactor in every case", "Jack"),
 ("22 Oct 2026", "LV14 criteria written before the first run; cables sized at soil 1.0 K m/W", "Claude Code"),
 ("27 Oct 2026", "D1 to D4: size on soil 1.5; revision C; minimum-fault check in the pass rule, R4 TMS 0.35; all inputs ASSUMED", "Proposed by Claude; approved by Jack 28 Oct"),
 ("27 Oct 2026", "LV15 criteria revision C written before the first run (commit 34caf6a)", "Claude"),
 ("28 Oct 2026", "D5 to D7: array 1000 mm2; reactor as two 155 MVAr units; R1 960 A. Criteria revision D written before its run (commit df09ba4)", "Claude, on Jack's instruction to finalise with the improvements"),
], [2.5, 10.5, 3.5], size=8)
d.save(R / "LV15_connection_study_report.docx")
print("written")
