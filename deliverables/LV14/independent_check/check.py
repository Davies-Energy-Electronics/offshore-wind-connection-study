"""Independent check of LV14 (Claude, 27 Oct 2026). Written from the stated inputs in RESULT.md and LV13 params.py,
without importing or reading the LV14 model code. Numpy and the standard library only.
Checks: (1) the 220 kV export cable rating, line by line; (2) the 66 kV maximum fault level, grid only, by hand.
Method forms are general knowledge (IEC 60287, IEC 60909 not read): NOT SOURCED to the standards."""
import math

ok = True
def same(name, mine, theirs, tol_pct):
    global ok
    err = abs(mine - theirs) / abs(theirs) * 100
    good = err <= tol_pct
    ok &= good
    print(f"{'PASS' if good else 'FAIL'}  {name}: mine {mine:.6g}, LV14 {theirs:.6g}, diff {err:.3f} % (tolerance {tol_pct} %)")

# ---- (1) export cable, 500 mm2 Cu, 220 kV, inputs as stated in RESULT.md (all ASSUMED there)
A, fill = 500e-6, 0.92
dc = math.sqrt(4 * A / (math.pi * fill)) * 1e3            # mm
t_ins, rho_ins, t_cov, rho_cov, rho_soil, L = 24.0, 3.5, 16.0, 6.0, 1.0, 1000.0
d_ins = dc + 2 * t_ins
d_lay = 2.155 * d_ins            # three touching cores laid up (general knowledge factor)
D_e = d_lay + 2 * t_cov
R20 = 1.7241e-8 / A
R90 = R20 * (1 + 0.00393 * 70)
f = 50.0
xs4 = (8 * math.pi * f / R90 * 1e-7 * 1.0) ** 2
ys = xs4 / (192 + 0.8 * xs4)
xp4 = (8 * math.pi * f / R90 * 1e-7 * 0.8) ** 2
Fp = xp4 / (192 + 0.8 * xp4)
k = dc / d_ins
yp = Fp * k ** 2 * (0.312 * k ** 2 + 1.18 / (Fp + 0.27))
R = R90 * (1 + ys + yp)
T1 = rho_ins / (2 * math.pi) * math.log(1 + 2 * t_ins / dc)
T3 = rho_cov / (2 * math.pi) * math.log(D_e / d_lay)
u = 2 * L / D_e
T4 = rho_soil / (2 * math.pi) * math.log(u + math.sqrt(u * u - 1))
eps = 2.5
C = 2 * math.pi * 8.854e-12 * eps / math.log(d_ins / dc)   # F/m
U0 = 220e3 / math.sqrt(3)
Wd = 2 * math.pi * f * C * U0 ** 2 * 0.001
num = 75.0 - 0.5 * Wd * T1 - 3 * Wd * (T3 + T4)
den = R * T1 + 3 * R * 1.1 * (T3 + T4)
I = math.sqrt(num / den)
same("conductor diameter (mm)", dc, 26.31, 0.1)
same("ys", ys, 0.0411, 1)
same("yp", yp, 0.0134, 1)
same("R at 90 C (uohm/m)", R * 1e6, 46.367, 0.05)
same("T1 (K m/W)", T1, 0.5784, 0.1)
same("T3 (K m/W)", T3, 0.1740, 0.5)
same("T4 (K m/W)", T4, 0.4828, 0.1)
same("C (nF/km)", C * 1e12, 133.94, 0.5)
same("Wd (W/m)", Wd, 0.6789, 0.5)
same("rating (A)", I, 759.6, 0.5)

# ---- (2) maximum three-phase fault at the offshore 66 kV bus, grid only, 100 MVA base (LV13 params.py values)
c, Sb = 1.1, 100.0
zg = c * Sb / 10000.0; xr = 10.0
Zg = complex(zg / math.hypot(1, xr), zg * xr / math.hypot(1, xr))
def trafo(n, s, uk, ur):
    z = uk / 100 * Sb / s; r = ur / 100 * Sb / s; x = math.sqrt(z * z - r * r)
    KT = 0.95 * c / (1 + 0.6 * (uk / 100 * math.sqrt(1 - (ur / uk) ** 2)))
    return complex(r, x) * KT / n, KT
Zon, KT = trafo(2, 250.0, 14.0, 0.30)
Zoss, _ = trafo(2, 250.0, 14.0, 0.30)
Zexp = complex(0.022, 0.125) * 60.0 / 2 / (220.0 ** 2 / Sb)
Z = Zg + Zon + Zexp + Zoss
Ik = c * Sb / (math.sqrt(3) * 66.0) / abs(Z)
print(f"K_T {KT:.4f}; Z total {Z.real:.5f} + j{Z.imag:.5f} pu, |Z| {abs(Z):.5f} pu")
same("Ik'' at OSS 66 kV, grid only (kA)", Ik, 13.226, 0.2)
print("ALL PASS" if ok else "SOME FAIL")
