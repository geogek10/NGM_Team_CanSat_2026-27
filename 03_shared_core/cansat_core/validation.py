from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from .constants import CSV_COLUMNS, P0_STD_HPA, SENSOR_BOUNDS
from .physics import compute_isa_altitude


def validate_live_packet(packet: Dict[str, float]) -> Tuple[bool, List[str]]:
    warnings: List[str] = []
    t_min, t_max = SENSOR_BOUNDS["temp_c"]
    if not (t_min <= packet.get("temp_c", -999) <= t_max):
        warnings.append("TEMP_OUT_OF_BOUNDS")
    p_min, p_max = SENSOR_BOUNDS["press_hpa"]
    if not (p_min <= packet.get("press_hpa", -999) <= p_max):
        warnings.append("PRESS_OUT_OF_BOUNDS")
    h_min, h_max = SENSOR_BOUNDS["hum_pct"]
    if not (h_min <= packet.get("hum_pct", -999) <= h_max):
        warnings.append("HUM_OUT_OF_BOUNDS")
    b_min, b_max = SENSOR_BOUNDS["batt_v"]
    if not (b_min <= packet.get("batt_v", 0) <= b_max):
        warnings.append("BATT_V_OUT_OF_BOUNDS")
    if packet.get("sats", 0) < SENSOR_BOUNDS["sats_min"]:
        warnings.append("LOW_GNSS_SATS")
    if packet.get("hdop", 99.0) > SENSOR_BOUNDS["hdop_max"]:
        warnings.append("HIGH_GNSS_HDOP")
    return (len(warnings) == 0), warnings


def detect_outliers_mad(values: np.ndarray, threshold: float = 3.5) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if len(arr) < 5:
        return np.zeros(len(arr), dtype=bool)
    median = np.nanmedian(arr)
    abs_dev = np.abs(arr - median)
    mad = np.nanmedian(abs_dev)
    if mad == 0.0 or np.isnan(mad):
        return np.zeros(len(arr), dtype=bool)
    modified_z = 0.6745 * abs_dev / mad
    return modified_z > threshold


def validate_flight_dataframe(df: pd.DataFrame, p0_hpa: float | None = None) -> Tuple[pd.DataFrame, Dict[str, object]]:
    missing_cols = [c for c in CSV_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required CSV columns: {missing_cols}")

    work_df = df.copy().sort_values("timestamp_ms").reset_index(drop=True)
    n_total = len(work_df)

    if p0_hpa is None:
        pre_launch = work_df[work_df["state"] == 0]["press_hpa"]
        p0_hpa = float(pre_launch.median()) if len(pre_launch) > 0 else P0_STD_HPA

    work_df["baro_alt_m"] = compute_isa_altitude(work_df["press_hpa"].values, p0_hpa=p0_hpa)

    t_min, t_max = SENSOR_BOUNDS["temp_c"]
    p_min, p_max = SENSOR_BOUNDS["press_hpa"]
    h_min, h_max = SENSOR_BOUNDS["hum_pct"]

    bounds_ok = (
        work_df["temp_c"].between(t_min, t_max)
        & work_df["press_hpa"].between(p_min, p_max)
        & work_df["hum_pct"].between(h_min, h_max)
    )

    dp = np.diff(work_df["press_hpa"].values, prepend=work_df["press_hpa"].iloc[0])
    dt_temp = np.diff(work_df["temp_c"].values, prepend=work_df["temp_c"].iloc[0])
    spike_mask = detect_outliers_mad(dp, threshold=6.0) | detect_outliers_mad(dt_temp, threshold=6.0)
    work_df["is_valid"] = bounds_ok & (~spike_mask)

    gnss_good = (
        work_df["is_valid"]
        & (work_df["sats"] >= SENSOR_BOUNDS["sats_min"])
        & (work_df["hdop"] <= SENSOR_BOUNDS["hdop_max"])
    )
    if gnss_good.sum() > 5:
        msl_offset = float(np.median(work_df.loc[gnss_good, "gps_alt_m"] - work_df.loc[gnss_good, "baro_alt_m"]))
        gps_agl = work_df.loc[gnss_good, "gps_alt_m"] - msl_offset
        baro_gps_mae = float(np.mean(np.abs(gps_agl - work_df.loc[gnss_good, "baro_alt_m"])))
    else:
        baro_gps_mae = -1.0

    valid_count = int(work_df["is_valid"].sum())
    integrity_score = round((valid_count / n_total) * 100.0, 2) if n_total > 0 else 0.0

    report = {
        "total_rows": n_total,
        "valid_rows": valid_count,
        "outlier_rows": int(spike_mask.sum()),
        "bounds_failed_rows": int((~bounds_ok).sum()),
        "integrity_score_pct": integrity_score,
        "p0_qfe_hpa": round(p0_hpa, 2),
        "baro_vs_gps_mae_m": round(baro_gps_mae, 2),
        "cross_sensor_passed": (0.0 <= baro_gps_mae <= 5.0),
    }
    return work_df, report
