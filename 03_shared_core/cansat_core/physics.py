from typing import Union
import numpy as np
from scipy.signal import savgol_filter
from .constants import BARO_EXPONENT, BARO_SCALE_ALT_M, P0_STD_HPA, R_SPECIFIC_AIR

Numeric = Union[float, np.ndarray]


def compute_isa_altitude(pressure_hpa: Numeric, p0_hpa: float = P0_STD_HPA) -> Numeric:
    is_scalar = np.ndim(pressure_hpa) == 0
    p = np.asarray(pressure_hpa, dtype=float)
    p_ratio = np.clip(p / float(p0_hpa), 1e-6, None)
    alt_m = BARO_SCALE_ALT_M * (1.0 - np.power(p_ratio, BARO_EXPONENT))
    return float(alt_m) if is_scalar else alt_m


def compute_air_density(pressure_hpa: Numeric, temp_c: Numeric) -> Numeric:
    is_scalar = np.ndim(pressure_hpa) == 0 and np.ndim(temp_c) == 0
    p_pa = np.asarray(pressure_hpa, dtype=float) * 100.0
    t_kelvin = np.clip(np.asarray(temp_c, dtype=float) + 273.15, 1.0, None)
    rho = p_pa / (R_SPECIFIC_AIR * t_kelvin)
    return float(rho) if is_scalar else rho


def compute_vertical_speed(
    altitudes_m: np.ndarray,
    timestamps_s: np.ndarray,
    window_length: int = 11,
    polyorder: int = 2,
) -> np.ndarray:
    alt = np.asarray(altitudes_m, dtype=float)
    t = np.asarray(timestamps_s, dtype=float)
    if len(alt) < 2:
        return np.zeros_like(alt)
    dt_diffs = np.diff(t)
    dt_median = float(np.median(dt_diffs)) if len(dt_diffs) > 0 else 0.0
    if len(alt) >= window_length and window_length % 2 == 1 and dt_median > 0:
        return savgol_filter(alt, window_length=window_length, polyorder=polyorder, deriv=1, delta=dt_median)
    return np.gradient(alt, t)


def compute_electrical_power(voltage_v: Numeric, current_a: Numeric) -> Numeric:
    is_scalar = np.ndim(voltage_v) == 0 and np.ndim(current_a) == 0
    power_w = np.asarray(voltage_v, dtype=float) * np.asarray(current_a, dtype=float)
    return float(power_w) if is_scalar else power_w
