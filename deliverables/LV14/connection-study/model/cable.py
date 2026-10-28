"""Continuous current rating of a buried three-core XLPE cable by a one-dimensional thermal circuit.

The form is the one IEC 60287 uses. IEC 60287 was NOT read: every formula below is written from general
knowledge and is NOT SOURCED to the standard text, and every input is ASSUMED. A design estimate, not a certified rating.

Heat from one core crosses its own insulation (T1); the heat of all three cores then crosses the coverings (T3) and the soil (T4).
    d_theta = (I^2 R + 0.5 Wd) T1 + (3 I^2 R (1 + lam) + 3 Wd) (T3 + T4)
    I = sqrt( (d_theta - 0.5 Wd T1 - 3 Wd (T3+T4)) / (R T1 + 3 R (1+lam) (T3+T4)) )
"""
import math
from dataclasses import dataclass, replace

EPS0 = 8.854187817e-12


@dataclass(frozen=True)
class Inputs:
    un_kv: float                # line voltage
    t_ins_mm: float             # XLPE insulation thickness
    area_mm2: float = 0.0
    f_hz: float = 50.0
    rho20: float = 1.7241e-8    # copper, ohm m at 20 C
    alpha20: float = 0.00393    # copper, per K
    fill: float = 0.92          # conductor area over circle area (compacted)
    ks: float = 1.0             # skin effect constant
    kp: float = 0.8             # proximity effect constant
    theta_max: float = 90.0     # conductor, C
    theta_amb: float = 15.0     # seabed, C
    rho_ins: float = 3.5        # K m/W, XLPE
    eps_r: float = 2.5
    tan_d: float = 0.001
    t_cov_mm: float = 16.0      # bedding + armour layer + serving, lumped
    rho_cov: float = 6.0        # K m/W, lumped
    rho_soil: float = 1.0       # K m/W
    depth_m: float = 1.0        # to cable axis
    lam: float = 0.10           # sheath + armour loss, as a fraction of conductor loss


def geometry(x):
    dc = math.sqrt(4 * x.area_mm2 / (math.pi * x.fill)) / 1000        # m
    t = x.t_ins_mm / 1000
    d_core = dc + 2 * t
    d_pre = (1 + 2 / math.sqrt(3)) * d_core                          # three touching cores
    d_ext = d_pre + 2 * x.t_cov_mm / 1000
    return dc, t, d_core, d_pre, d_ext


def r_ac(x, theta):
    """AC resistance per metre at conductor temperature theta (ohm/m), with skin and proximity factors."""
    dc, t, d_core, _, _ = geometry(x)
    rdc = x.rho20 / (x.area_mm2 * 1e-6) * (1 + x.alpha20 * (theta - 20))
    xs4 = (8 * math.pi * x.f_hz / rdc * 1e-7 * x.ks) ** 2
    ys = xs4 / (192 + 0.8 * xs4)
    xp4 = (8 * math.pi * x.f_hz / rdc * 1e-7 * x.kp) ** 2
    g = xp4 / (192 + 0.8 * xp4)
    r = dc / d_core                                                  # dc / s
    yp = g * r ** 2 * (0.312 * r ** 2 + 1.18 / (g + 0.27))
    return rdc * (1 + ys + yp), rdc, ys, yp


def parts(x):
    dc, t, d_core, d_pre, d_ext = geometry(x)
    t1 = x.rho_ins / (2 * math.pi) * math.log(1 + 2 * t / dc)
    t3 = x.rho_cov / (2 * math.pi) * math.log(d_ext / d_pre)
    u = 2 * x.depth_m / d_ext
    t4 = x.rho_soil / (2 * math.pi) * math.log(u + math.sqrt(u * u - 1))
    c = 2 * math.pi * EPS0 * x.eps_r / math.log(1 + 2 * t / dc)      # F/m per core
    u0 = x.un_kv * 1e3 / math.sqrt(3)
    wd = 2 * math.pi * x.f_hz * c * u0 ** 2 * x.tan_d                # W/m per core
    r, rdc, ys, yp = r_ac(x, x.theta_max)
    return dict(dc_mm=dc * 1e3, d_ext_mm=d_ext * 1e3, T1=t1, T3=t3, T4=t4, c_nf_per_km=c * 1e12, Wd=wd,
                R_uohm_m=r * 1e6, Rdc_uohm_m=rdc * 1e6, ys=ys, yp=yp, R_ohm_km=r * 1e3)


def rating_a(x):
    p = parts(x)
    d_theta = x.theta_max - x.theta_amb
    text = p["T3"] + p["T4"]
    r = p["R_uohm_m"] * 1e-6
    num = d_theta - 0.5 * p["Wd"] * p["T1"] - 3 * p["Wd"] * text
    den = r * p["T1"] + 3 * r * (1 + x.lam) * text
    return math.sqrt(num / den), p


SERIES = [95, 120, 150, 185, 240, 300, 400, 500, 630, 800, 1000, 1200, 1400, 1600, 2000]


def smallest(x, design_a, series=SERIES):
    for a in series:
        i, p = rating_a(replace(x, area_mm2=a))
        if i >= design_a:
            return a, i, p
    return None, None, None
