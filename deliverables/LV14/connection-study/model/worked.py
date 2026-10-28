"""Whiteboard worked example: the export cable rating, step by step, from cable.py's own parts. Prints and saves results/worked_example.txt."""
import math
from pathlib import Path
from cable import Inputs, parts, rating_a
from dataclasses import replace

x = replace(Inputs(un_kv=220.0, t_ins_mm=24.0), area_mm2=500)
p = parts(x)
dth = x.theta_max - x.theta_amb
text = p["T3"] + p["T4"]
r = p["R_uohm_m"] * 1e-6
num = dth - 0.5 * p["Wd"] * p["T1"] - 3 * p["Wd"] * text
den = r * p["T1"] + 3 * r * (1 + x.lam) * text
L = [
 "WORKED EXAMPLE: 220 kV export cable, 500 mm2 copper, three-core XLPE, buried 1.0 m. All inputs ASSUMED; IEC 60287 NOT read.",
 f"1 Temperature rise available: {x.theta_max} - {x.theta_amb} = {dth} K",
 f"2 Conductor diameter from area: sqrt(4 x 500 / (pi x 0.92)) = {p['dc_mm']:.2f} mm",
 f"3 AC resistance at 90 C: Rdc20 = 1.7241e-8 / 500e-6 = {1.7241e-8/500e-6*1e6:.2f} uohm/m; x(1+0.00393 x 70) = {p['Rdc_uohm_m']:.3f} uohm/m; x(1 + ys {p['ys']:.4f} + yp {p['yp']:.4f}) = {p['R_uohm_m']:.3f} uohm/m",
 f"4 Insulation: T1 = 3.5/(2 pi) x ln(1 + 2 x 24 / {p['dc_mm']:.2f}) = {p['T1']:.4f} K m/W",
 f"5 Coverings: outer diameter {p['d_ext_mm']:.1f} mm; T3 = 6.0/(2 pi) x ln(Dext / Dpre) = {p['T3']:.4f} K m/W",
 f"6 Soil: u = 2 x 1.0 / {p['d_ext_mm']/1000:.4f} = {2/(p['d_ext_mm']/1000):.3f}; T4 = 1.0/(2 pi) x ln(u + sqrt(u^2 - 1)) = {p['T4']:.4f} K m/W",
 f"7 Dielectric loss per core: Wd = w C U0^2 tan d, C = {p['c_nf_per_km']:.2f} nF/km, = {p['Wd']:.4f} W/m",
 f"8 Numerator: {dth} - 0.5 x {p['Wd']:.4f} x {p['T1']:.4f} - 3 x {p['Wd']:.4f} x {text:.4f} = {num:.4f}",
 f"9 Denominator: R T1 + 3 R (1 + {x.lam}) (T3 + T4) = {den:.4e}",
 f"10 I = sqrt({num:.4f} / {den:.4e}) = {math.sqrt(num/den):.1f} A   (cable.py: {rating_a(x)[0]:.1f} A)",
]
txt = "\n".join(L)
print(txt)
Path(__file__).resolve().parents[1].joinpath("results", "worked_example.txt").write_text(txt + "\n")
