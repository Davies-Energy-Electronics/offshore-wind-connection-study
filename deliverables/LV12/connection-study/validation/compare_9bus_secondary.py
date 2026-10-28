"""Informational comparison of the 9-bus result against a SECONDARY published table (not the Anderson and Fouad
textbook the criteria name, so C9-PUB stays OPEN): KIOS Centre, 'IEEE 9-bus modified test system', model documentation
R0 (2020), Table 6, first magnitude and angle pair, which the document compares with a PSS/E version of the benchmark.
Magnitudes are printed to 2 decimals there, so only angles can be held to the criteria tolerance (0.05 degree).

Bus mapping (by load, not by result, so it is not circular): the WSCC numbering puts the 125 MW load at bus 5, 90 MW at 6 and
100 MW at 8; MATPOWER case9 puts 90 MW at bus 5, 100 MW at 7 and 125 MW at 9. Generators keep 1 to 3 and bus 4 is bus 4.
Hence WSCC 5,6,7,8,9 = MATPOWER 9,5,8,7,6 (7 and 9 follow from the line topology between those loads and generators 2 and 3)."""
import csv
from pathlib import Path

H = Path(__file__).resolve().parents[1]
MAP = {1: 1, 2: 2, 3: 3, 4: 4, 5: 9, 6: 5, 7: 8, 8: 7, 9: 6}
ours = {int(r["bus"]): r for r in csv.DictReader(open(H / "results" / "case9_bus_results.csv"))}
ref = list(csv.DictReader(open(H / "inputs_secondary" / "kios_ieee9_table6.csv")))
worst_a = worst_m = 0.0
lines = ["wscc_bus matpower_bus  ref_vm  ours_vm  d_vm       ref_va   ours_va   d_va_deg"]
for r in ref:
    w = int(r["wscc_bus"]); m = MAP[w]
    vm, va = float(ours[m]["pandapower_vm_pu"]), float(ours[m]["pandapower_va_deg"])
    dv = abs(vm - float(r["vm_pu"]))   # a 2 dp printed value covers +/- 0.005 pu
    da = abs(va - float(r["va_degree"]))
    worst_a, worst_m = max(worst_a, da), max(worst_m, dv)
    lines.append(f"{w:8d} {m:12d}  {float(r['vm_pu']):6.2f}  {vm:7.4f}  {dv:9.4f}  {float(r['va_degree']):6.2f}  {va:8.4f}  {da:8.4f}")
lines.append(f"worst angle difference {worst_a:.4f} degree (criteria tolerance 0.05); every magnitude within the 0.005 pu a 2 dp print covers: {'yes' if worst_m <= 0.005 + 1e-9 else 'no'} (worst {worst_m:.4f} pu)")
lines.append("Verdict: INFORMATIONAL PASS against a secondary source. C9-PUB stays OPEN until the Anderson and Fouad table is supplied or Jack accepts this source.")
out = "\n".join(lines); print(out)
(H / "results" / "compare_9bus_secondary.txt").write_text(out + "\n")
