"""
Generate a realistic synthetic 2-Stage CanSat-to-Drone flight dataset:
- Stage 1: Rocket launch (0 -> 950m AGL) + Parachute descent (with wind drift & 2 sensor spikes)
- Stage 2: Post-recovery Drone Scout takeoff (8m AGL) flying over a simulated VOC crater!

Outputs:
- 05_neural_networks/datasets/sample_flight.csv
- docs/sample_flight.kml (ready to open in Google Earth / Earth Studio!)
"""

from pathlib import Path
import numpy as np
import pandas as pd

from cansat_core import (
    CSV_COLUMNS,
    MissionStage,
    MissionState,
    export_mission_to_kml,
    validate_flight_dataframe,
)


def _alt_to_pressure_hpa(alt_agl_m: np.ndarray, p0_hpa: float = 1005.0) -> np.ndarray:
    """Inverse ISA barometric formula."""
    return p0_hpa * np.power(np.clip(1.0 - (alt_agl_m / 44330.0), 1e-3, None), 5.2559)


def generate_mock_mission(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Launchpad location (e.g., near Thessaloniki / launch field, elevation 50m MSL)
    base_lat = 40.630000
    base_lon = 22.950000
    ground_msl = 50.0
    p0_hpa = 1005.0
    t_ground_c = 22.0

    rows = []
    t_ms = 0

    def add_segment(
        n_steps: int,
        dt_ms: int,
        stage: MissionStage,
        state: MissionState,
        alt_arr: np.ndarray,
        lat_arr: np.ndarray,
        lon_arr: np.ndarray,
        acc_arr: np.ndarray,
        batt_arr: np.ndarray,
        curr_arr: np.ndarray,
        voc_drop_mask: np.ndarray | None = None,
    ) -> None:
        nonlocal t_ms
        press_arr = _alt_to_pressure_hpa(alt_arr, p0_hpa=p0_hpa) + rng.normal(0, 0.08, n_steps)
        temp_arr = t_ground_c - 0.0065 * alt_arr + rng.normal(0, 0.12, n_steps)
        hum_arr = np.clip(52.0 + 0.01 * alt_arr + rng.normal(0, 0.4, n_steps), 0, 100)

        # Clean baseline gas resistance varies slightly with temp & humidity
        voc_r1 = 180_000.0 - 500.0 * (temp_arr - 20.0) + rng.normal(0, 1200, n_steps)
        voc_r2 = 145_000.0 - 400.0 * (temp_arr - 20.0) + rng.normal(0, 1000, n_steps)

        if voc_drop_mask is not None:
            # Simulate VOC plume over crater (MOX resistance drops sharply)
            voc_r1 = np.where(voc_drop_mask, voc_r1 * 0.48, voc_r1)
            voc_r2 = np.where(voc_drop_mask, voc_r2 * 0.35, voc_r2)

        for i in range(n_steps):
            rows.append({
                "timestamp_ms": int(t_ms),
                "stage": int(stage),
                "state": int(state),
                "lat": float(lat_arr[i]),
                "lon": float(lon_arr[i]),
                "gps_alt_m": float(ground_msl + alt_arr[i] + rng.normal(0, 0.6)),
                "sats": int(18 if state != MissionState.PRE_LAUNCH else 12),
                "hdop": round(float(rng.uniform(0.7, 1.1)), 2),
                "press_hpa": round(float(press_arr[i]), 2),
                "temp_c": round(float(temp_arr[i]), 2),
                "hum_pct": round(float(hum_arr[i]), 2),
                "voc_r1_ohm": round(float(voc_r1[i]), 1),
                "voc_r2_ohm": round(float(voc_r2[i]), 1),
                "roll_deg": round(float(rng.normal(0, 2.5 if stage == 2 else 8.0)), 2),
                "pitch_deg": round(float(rng.normal(0, 2.5 if stage == 2 else 8.0)), 2),
                "yaw_deg": round(float((i * 3) % 360), 1),
                "acc_g": round(float(acc_arr[i]), 2),
                "batt_v": round(float(batt_arr[i]), 2),
                "curr_a": round(float(curr_arr[i]), 2),
                "lq_pct": int(rng.integers(94, 101)),
            })
            t_ms += dt_ms

    # 1. Pre-Launch (5 sec @ 2Hz)
    add_segment(
        10, 500, MissionStage.STAGE_1_CANSAT_DESCENT, MissionState.PRE_LAUNCH,
        np.zeros(10), np.full(10, base_lat), np.full(10, base_lon),
        np.full(10, 1.0), np.full(10, 16.70), np.full(10, 0.15),
    )

    # 2. Rocket Launch (10 sec @ 5Hz: 0 -> 950m)
    n_launch = 50
    alt_up = np.linspace(0, 950, n_launch)
    lat_up = np.linspace(base_lat, base_lat + 0.0004, n_launch)
    lon_up = np.linspace(base_lon, base_lon + 0.0005, n_launch)
    add_segment(
        n_launch, 200, MissionStage.STAGE_1_CANSAT_DESCENT, MissionState.LAUNCH,
        alt_up, lat_up, lon_up,
        np.full(n_launch, 4.8), np.full(n_launch, 16.68), np.full(n_launch, 0.18),
    )

    # 3. Parachute Descent (110 sec @ 2Hz: 950m -> 0m with wind drift)
    n_desc = 220
    alt_dn = np.linspace(950, 0, n_desc)
    land_lat = base_lat + 0.0018
    land_lon = base_lon + 0.0022
    lat_dn = np.linspace(lat_up[-1], land_lat, n_desc)
    lon_dn = np.linspace(lon_up[-1], land_lon, n_desc)
    add_segment(
        n_desc, 500, MissionStage.STAGE_1_CANSAT_DESCENT, MissionState.PARACHUTE_DESCENT,
        alt_dn, lat_dn, lon_dn,
        np.full(n_desc, 1.02), np.linspace(16.65, 16.55, n_desc), np.full(n_desc, 0.18),
    )

    # 4. Touchdown & Recovery pause (6 sec @ 1Hz)
    add_segment(
        6, 1000, MissionStage.STAGE_1_CANSAT_DESCENT, MissionState.TOUCHDOWN_RECOVERY,
        np.zeros(6), np.full(6, land_lat), np.full(6, land_lon),
        np.full(6, 1.0), np.full(6, 16.54), np.full(6, 0.15),
    )

    # 5. Stage 2: Drone Scout Flight after recovery (40 sec @ 5Hz = 200 steps)
    # Flies a rectangular patrol 8m AGL over a simulated crater with a VOC plume!
    n_drone = 200
    t_norm = np.linspace(0, 1, n_drone)
    alt_drone = np.piecewise(
        t_norm,
        [t_norm < 0.15, (t_norm >= 0.15) & (t_norm <= 0.85), t_norm > 0.85],
        [lambda x: (x / 0.15) * 8.0, 8.0, lambda x: ((1.0 - x) / 0.15) * 8.0],
    )
    # Square scout loop (~40m x 40m)
    angle = t_norm * 2 * np.pi
    lat_drone = land_lat + 0.00018 * np.sin(angle)
    lon_drone = land_lon + 0.00022 * (1 - np.cos(angle))
    # Crater/plume located around 35% - 55% of the drone flight
    plume_mask = (t_norm >= 0.35) & (t_norm <= 0.55)
    curr_drone = np.where(alt_drone > 0.5, rng.normal(14.5, 1.2, n_drone), 0.2)
    batt_drone = np.linspace(16.45, 15.10, n_drone)

    add_segment(
        n_drone, 200, MissionStage.STAGE_2_DRONE_SCOUT, MissionState.DRONE_SCOUT,
        alt_drone, lat_drone, lon_drone,
        rng.normal(1.05, 0.08, n_drone), batt_drone, curr_drone,
        voc_drop_mask=plume_mask,
    )

    df = pd.DataFrame(rows, columns=CSV_COLUMNS)

    # Inject 2 artificial sensor spikes during descent to test MAD outlier filter!
    df.loc[120, "temp_c"] = 999.0
    df.loc[180, "press_hpa"] = 150.0
    return df


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    csv_out = repo_root / "05_neural_networks" / "datasets" / "sample_flight.csv"
    kml_out = repo_root / "docs" / "sample_flight.kml"

    raw_df = generate_mock_mission()
    raw_df.to_csv(csv_out, index=False)

    clean_df, report = validate_flight_dataframe(raw_df)
    export_mission_to_kml(clean_df, kml_out)

    print(f"[OK] Saved mock flight CSV -> {csv_out}")
    print(f"[OK] Saved Google Earth 3D KML -> {kml_out}")
    print("[Validation Report]:", report)