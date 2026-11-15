from enum import IntEnum


class MissionStage(IntEnum):
    STAGE_1_CANSAT_DESCENT = 1
    STAGE_2_DRONE_SCOUT = 2


class MissionState(IntEnum):
    PRE_LAUNCH = 0
    LAUNCH = 1
    PARACHUTE_DESCENT = 2
    TOUCHDOWN_RECOVERY = 3
    GROUND_TRANSFORM = 4
    DRONE_SCOUT = 5


P0_STD_HPA = 1013.25
T0_STD_K = 288.15
LAPSE_RATE_K_M = 0.0065
GRAVITY_MS2 = 9.80665
MOLAR_MASS_AIR = 0.0289644
GAS_CONSTANT_R = 8.31447
R_SPECIFIC_AIR = 287.058

BARO_SCALE_ALT_M = 44330.0
BARO_EXPONENT = 1.0 / 5.2559

BATTERY_CELLS = 4
BATTERY_CAP_MAH = 650
BATTERY_C_RATING = 120
CELL_V_FULL = 4.20
CELL_V_WARN = 3.45
CELL_V_CRIT = 3.30
MOTOR_POLES = 14
MAX_MASS_G = 350.0

SENSOR_BOUNDS = {
    "temp_c": (-40.0, 85.0),
    "press_hpa": (300.0, 1100.0),
    "hum_pct": (0.0, 100.0),
    "voc_ohm": (100.0, 50_000_000.0),
    "batt_v": (10.0, 17.5),
    "curr_a": (0.0, 80.0),
    "hdop_max": 2.5,
    "sats_min": 6,
}

CSV_COLUMNS = [
    "timestamp_ms", "stage", "state", "lat", "lon", "gps_alt_m",
    "sats", "hdop", "press_hpa", "temp_c", "hum_pct",
    "voc_r1_ohm", "voc_r2_ohm", "roll_deg", "pitch_deg", "yaw_deg",
    "acc_g", "batt_v", "curr_a", "lq_pct",
]
