from pathlib import Path
import numpy as np
import pandas as pd
from cansat_core import CSV_COLUMNS, MissionStage, MissionState, export_mission_to_kml, validate_flight_dataframe


def _alt_to_pressure_hpa(alt_agl_m: np.ndarray, p0_hpa: float = 1005.0) -> np.ndarray:
    return p0_hpa * np.power(np.clip(1.0 - (alt_agl_m / 44330.0), 1e-3, None), 5.2559)


def generate_mock_mission(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base_lat, base_lon, ground_msl, p0_hpa, t_ground_c = 40.630000, 22.950000, 50.0, 1005.0, 22.0
    rows, t_ms = [], 0

    def add_segment(n_steps, dt_ms, stage, state, alt_arr, lat_arr, lon_arr, acc_arr, batt_arr, curr_arr, voc_drop_mask=None):
        nonlocal t_ms
        press_arr = _alt_to_pressure_hpa(alt_arr, p0_hpa=p0_hpa) + rng.normal(0, 0.08, n_steps)
        temp_arr = t_ground_c - 0.0065 * alt_arr + rng.normal(0, 0.12, n_steps)
        hum_arr = np.clip(52.0 + 0.01 * alt_arr + rng.normal(0, 0.4, n_steps), 0, 100)
        voc_r1 = 180_000.0 - 500.0 * (temp_arr - 20.0) + rng.normal(0, 1200, n_steps)
        voc_r2 = 145_000.0 - 400.0 * (temp_arr - 20.0) + rng.normal(0, 1000, n_steps)
        if voc_drop_mask is not None:
            voc_r1 = np.where(voc_drop_mask, voc_r1 * 0.48, voc_r1)
            voc_r2 = np.where(voc_drop_mask, voc_r2 * 0.35, voc_r2)
        for i in range(n_steps):
            rows.append({
                "timestamp_ms": int(t_ms), "stage": int(stage), "state": int(state),
                "lat": float(lat_arr[i]), "lon": float(lon_arr[i]),
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

    add_segment(10, 500, MissionStage.STAGE_1_CANSAT_DESCENT, MissionState.PRE_LAUNCH,
                np.zeros(10), np.full(10, base_lat), np.full(10, base_lon),
                np.full(10, 1.0), np.full(10, 16.70), np.full(10, 0.15))

    n_launch = 50
    alt_up = np.linspace(0, 950, n_launch)
    lat_up = np.linspace(base_lat, base_lat + 0.0004, n_launch)
    lon_up = np.linspace(base_lon, base_lon + 0.0005, n_launch)
    add_segment(n_launch, 200, MissionStage.STAGE_1_CANSAT_DESCENT, MissionState.LAUNCH,
                alt_up, lat_up, lon_up, np.full(n_launch, 4.8), np.full(n_launch, 16.68), np.full(n_launch, 0.18))

    n_desc = 220
    alt_dn = np.linspace(950, 0, n_desc)
    land_lat, land_lon = base_lat + 0.0018, base_lon + 0.0022
    add_segment(n_desc, 500, MissionStage.STAGE_1_CANSAT_DESCENT, MissionState.PARACHUTE_DESCENT,
                alt_dn, np.linspace(lat_up[-1], land_lat, n_desc), np.linspace(lon_up[-1], land_lon, n_desc),
                np.full(n_desc, 1.02), np.linspace(16.65, 16.55, n_desc), np.full(n_desc, 0.18))

    add_segment(6, 1000, MissionStage.STAGE_1_CANSAT_DESCENT, MissionState.TOUCHDOWN_RECOVERY,
                np.zeros(6), np.full(6, land_lat), np.full(6, land_lon),
                np.full(6, 1.0), np.full(6, 16.54), np.full(6, 0.15))

    n_drone = 200
    t_norm = np.linspace(0, 1, n_drone)
    alt_drone = np.piecewise(t_norm, [t_norm < 0.15, (t_norm >= 0.15) & (t_norm <= 0.85), t_norm > 0.85],
                             [lambda x: (x / 0.15) * 8.0, 8.0, lambda x: ((1.0 - x) / 0.15) * 8.0])
    angle = t_norm * 2 * np.pi
    lat_drone = land_lat + 0.00018 * np.sin(angle)
    lon_drone = land_lon + 0.00022 * (1 - np.cos(angle))
    plume_mask = (t_norm >= 0.35) & (t_norm <= 0.55)
    curr_drone = np.where(alt_drone > 0.5, rng.normal(14.5, 1.2, n_drone), 0.2)
    add_segment(n_drone, 200, MissionStage.STAGE_2_DRONE_SCOUT, MissionState.DRONE_SCOUT,
                alt_drone, lat_drone, lon_drone, rng.normal(1.05, 0.08, n_drone),
                np.linspace(16.45, 15.10, n_drone), curr_drone, voc_drop_mask=plume_mask)

    df = pd.DataFrame(rows, columns=CSV_COLUMNS)
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
    print(f"[OK] Saved Google Eart
cat << 'EOF' > README.md
# NGM Team CanSat 2026–27 — Planetary Aerial Scout

Open-source software architecture for the **NGM Team Hybrid Drone-CanSat**, designed for the ESA CanSat competition.

## Mission Concept
1. **Stage 1 — Atmospheric CanSat Descent:** Launched inside a 66mm x 115mm (<350g) rocket payload bay, descending by parachute with motors strictly **DISARMED** while capturing vertical atmospheric profiles (Temperature, Pressure, Humidity, VOCs, GNSS).
2. **Stage 2 — Post-Recovery Planetary Drone Scout:** After landing and recovery, the folded arms deploy and the CanSat transforms into an autonomous quadcopter capable of flying over craters, trenches, and rocky terrain where wheeled rovers fail, performing low-altitude spatial gas scanning and **Habitability Index** assessment.

## Repository Structure
| Folder | Description |
| :--- | :--- |
| `01_firmware/` | Custom INAV (`STM32G473 @ 170MHz`) BME688 VOC driver, State Machine & Bluejay ESC configs |
| `02_radio_controller/` | `RadioMaster Boxer` (EdgeTX) Lua HUD (`cansat.lua`), voice alerts & switch mappings |
| `03_shared_core/` | Reusable Python package (`cansat_core`): ISA physics, 4-stage validation & KML exporter |
| `04_field_gcs_scada/` | Field laptop app: USB-C MAVLink ingestor, live 60FPS plots & SCADA monitoring/alarms |
| `05_neural_networks/` | PyTorch/ONNX training pipeline (`GasSpecNet`, `HabitabilityNet`, `AeroHealthNet`) |
| `06_web_dashboard/` | TerraPulse-style Full-Stack Web App (`FastAPI` + `React/ECharts/Deck.gl`) |
| `07_tools_and_tests/` | Mock 2-stage flight simulator (hardware-free testing) & `pytest` unit tests |
| `docs/` | Wiring diagrams, software architecture docs & Google Earth Studio 3D `.kml` exports |

## Quickstart (Local Setup)
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ./03_shared_core
    pip install pytest
    python3 07_tools_and_tests/mock_flight_generator.py
    pytest 07_tools_and_tests/tests/
