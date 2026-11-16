"""
Κοινές σταθερές, ενιαία μορφή CSV (20 στήλες) & εξισώσεις φυσικής
για το πρόγραμμα λήψης πεδίου (receiver).
"""

import math
from typing import Dict, List, Tuple

# Οι 6 φάσεις της αποστολής (αντιστοιχούν στον κώδικα C του sender)
STATE_NAMES = {
    0: "PRE_LAUNCH",
    1: "LAUNCH",
    2: "PARACHUTE_DESCENT",
    3: "TOUCHDOWN_RECOVERY",
    4: "GROUND_TRANSFORM",
    5: "DRONE_SCOUT",
}

# Η ΕΝΙΑΙΑ μορφή CSV (ακριβώς οι ίδιες 20 στήλες που δέχεται το data_analysis_app!)
CSV_COLUMNS = [
    "timestamp_ms", "stage", "state", "lat", "lon", "gps_alt_m",
    "sats", "hdop", "press_hpa", "temp_c", "hum_pct",
    "voc_r1_ohm", "voc_r2_ohm", "roll_deg", "pitch_deg", "yaw_deg",
    "acc_g", "batt_v", "curr_a", "lq_pct",
]

BATTERY_CELLS = 4       # Μπαταρία GNB 4S (4 κυψέλες σε σειρά)
CELL_V_WARN = 3.45      # Προειδοποίηση SCADA στα 3.45V ανά κυψέλη
CELL_V_CRIT = 3.30      # Κρίσιμος συναγερμός στα 3.30V ανά κυψέλη


def compute_isa_altitude(press_hpa: float, p0_hpa: float = 1013.25) -> float:
    """Υπολογίζει το σχετικό υψόμετρο (m) από την πίεση με τον Διεθνή Τύπο ISA."""
    ratio = max(1e-6, float(press_hpa) / float(p0_hpa))  # Αποφυγή αρνητικού/μηδενικού λόγου
    return 44330.0 * (1.0 - math.pow(ratio, 1.0 / 5.2559))


def validate_live_packet(pkt: Dict[str, float]) -> Tuple[bool, List[str]]:
    """Ελέγχει αν ένα ζωντανό πακέτο έχει φυσιολογικές τιμές αισθητήρων."""
    warns: List[str] = []
    if not (-40.0 <= pkt.get("temp_c", -999) <= 85.0):     # Όρια BME688 θερμοκρασίας
        warns.append("TEMP_OUT_OF_BOUNDS")
    if not (300.0 <= pkt.get("press_hpa", -999) <= 1100.0): # Όρια BME688 πίεσης
        warns.append("PRESS_OUT_OF_BOUNDS")
    if not (0.0 <= pkt.get("hum_pct", -999) <= 100.0):      # Όρια υγρασίας 0-100%
        warns.append("HUM_OUT_OF_BOUNDS")
    if pkt.get("sats", 0) < 6:                              # Ελάχιστοι 6 δορυφόροι
        warns.append("LOW_GNSS_SATS")
    return (len(warns) == 0), warns
