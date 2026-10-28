"""Single-line diagram of revision C, drawn with matplotlib (no CAD). Writes results/sld.png and results/sld.svg."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import revc

R = Path(__file__).resolve().parents[1] / "results"
S = revc.SIZED
fig, ax = plt.subplots(figsize=(15, 6.2))
ax.set_xlim(0, 30); ax.set_ylim(0, 12.4); ax.axis("off")
K = dict(color="black", lw=1.4)


def bus(x, y0, y1, label, sub):
    ax.plot([x, x], [y0, y1], color="black", lw=4)
    ax.text(x, y1 + 0.35, label, ha="center", va="bottom", fontsize=9, weight="bold")
    ax.text(x, y0 - 0.35, sub, ha="center", va="top", fontsize=7.5)


def trafo(x, y, label=None):
    ax.add_patch(Circle((x - 0.28, y), 0.42, fill=False, lw=1.3)); ax.add_patch(Circle((x + 0.28, y), 0.42, fill=False, lw=1.3))
    if label: ax.text(x, y - 0.65, label, ha="center", va="top", fontsize=7)


def breaker(x, y, tag=None):
    ax.add_patch(Rectangle((x - 0.17, y - 0.17), 0.34, 0.34, fill=True, color="white", ec="black", lw=1.2))
    if tag: ax.text(x, y + 0.3, tag, ha="center", va="bottom", fontsize=7.5, color="#b00020", weight="bold")


# grid
ax.add_patch(Circle((1.2, 6.2), 0.7, fill=False, lw=1.4)); ax.text(1.2, 6.2, "Grid", ha="center", va="center", fontsize=8)
ax.text(1.2, 5.1, "10 GVA max\n5 GVA min\nX/R 10", ha="center", va="top", fontsize=7)
ax.plot([1.9, 3.2], [6.2, 6.2], **K)
bus(3.2, 3.6, 8.8, "PCC 400 kV", "limits 0.95 to 1.05 pu")
# onshore transformers
for y, n in ((7.6, "T_ON1"), (4.8, "T_ON2")):
    ax.plot([3.2, 4.2], [y, y], **K); breaker(4.2, y, "R4" if n == "T_ON1" else None); ax.plot([4.4, 5.3], [y, y], **K)
    trafo(5.85, y, f"{n} 400/220 kV\n250 MVA, 14 %"); ax.plot([6.55, 7.6], [y, y], **K)
bus(7.6, 3.6, 8.8, "Onshore 220 kV", "")
ax.plot([7.6, 8.5], [2.9 + 0.7, 2.9 + 0.7], **K)
ax.plot([8.5, 8.5], [3.6, 2.6], **K)
for k in range(3):
    ax.add_patch(matplotlib.patches.Arc((8.5, 2.45 - 0.3 * k), 0.3, 0.3, theta1=270, theta2=90, lw=1.2))
ax.text(8.9, 2.1, "Reactor 2 x 155 MVAr\n(D6)" if revc.REV == "D" else "Reactor 310 MVAr\n(one unit)", fontsize=7, va="center")
# export cables
for y, n in ((7.6, "EXP1"), (4.8, "EXP2")):
    breaker(8.4, y, "R3" if n == "EXP1" else None); ax.plot([7.6, 8.2], [y, y], **K); ax.plot([8.6, 13.4], [y, y], **K)
    ax.plot([12.4, 12.6, 12.8], [y - 0.15, y + 0.15, y - 0.15], color="black", lw=1.0)
    ax.text(8.9, y + 0.25, f"{n}: 60 km, 220 kV 3-core XLPE\n{S['export']['area_mm2']} mm2 Cu, {S['export']['rating_a']:.0f} A", fontsize=7, va="bottom")
ax.text(11.0, 6.2, "subsea", fontsize=7, style="italic", ha="left")
bus(13.4, 3.6, 8.8, "OSS 220 kV", "offshore substation")
for y, n in ((7.6, "T_OSS1"), (4.8, "T_OSS2")):
    ax.plot([13.4, 14.5], [y, y], **K); trafo(15.05, y, f"{n} 220/66 kV\n250 MVA, 14 %"); ax.plot([15.75, 16.4], [y, y], **K)
    breaker(16.4, y, "R2" if n == "T_OSS1" else None); ax.plot([16.6, 17.4], [y, y], **K)
bus(17.4, 1.4, 11.0, "OSS 66 kV", "")
# strings
ys = [10.2, 8.3, 6.4, 4.5, 2.6]
for i, y in enumerate(ys, 1):
    ax.plot([17.4, 18.2], [y, y], **K); breaker(18.4, y, ("R1 960 A" if revc.REV == "D" else "R1") if i == 1 else None); ax.plot([18.6, 19.6], [y, y], **K)
    xs = [19.6 + 1.2 * j for j in range(8)]
    ax.plot([19.6, xs[-1]], [y, y], **K)
    for j, x in enumerate(xs):
        ax.plot([x, x], [y, y - 0.45], color="black", lw=1.0)
        ax.add_patch(Circle((x, y - 0.68), 0.23, fill=False, lw=1.0)); ax.text(x, y - 0.68, "~", ha="center", va="center", fontsize=7)
    ax.text(xs[-1] + 0.45, y, f"String {i}", fontsize=7.5, va="center")
ax.text(23.8, 11.35, f"5 strings x 8 turbines x 10 MW = 400 MW. Array: 66 kV {S['array']['area_mm2']} mm2 Cu XLPE, {S['array']['rating_a']:.0f} A;\nOSS to first turbine 2.5 km, then 1.2 km between turbines",
        ha="center", fontsize=7.5)
foot = ("Revision D, the final base design (LV15). Self-directed study on ASSUMED data, not a design for construction. Ratings at soil 1.5 K m/W (D1). "
        "R1 to R4: overcurrent relays (LV14); R1 pickup 960 A (D7), R4 TMS 0.35 (D3). Turbine transformers omitted (LV13 A05).") if revc.REV == "D" else (
        "Revision C, LV15. Self-directed study on ASSUMED data, not a design for construction. Ratings at soil 1.5 K m/W (decision D1). "
        "R1 to R4: overcurrent relays (LV14), R4 TMS 0.35 (decision D3). Turbine transformers omitted (LV13 A05).")
ax.text(0.2, 0.25, foot, fontsize=7, color="#444")
fig.tight_layout()
name = "sld" if revc.REV == "D" else "sld_C"
fig.savefig(R / f"{name}.png", dpi=180); fig.savefig(R / f"{name}.svg")
print("written", name)
