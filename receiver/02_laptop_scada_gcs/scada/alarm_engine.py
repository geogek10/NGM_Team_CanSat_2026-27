from dataclasses import dataclass
from typing import Dict, List
from core.cansat_physics import BATTERY_CELLS, CELL_V_CRIT, CELL_V_WARN, validate_live_packet


@dataclass
class ScadaAlarm:
    timestamp_ms: int  # Χρόνος συμβάντος (ms)
    severity: str      # Επίπεδο: "INFO", "WARN", "CRIT"
    code: str          # Κωδικός συναγερμού (π.χ. "VOC_PLUME")
    message: str       # Περιγραφή στα Αγγλικά/Ελληνικά για την οθόνη


class ScadaAlarmEngine:
    """Επιβλέπει κάθε εισερχόμενο πακέτο και παράγει συναγερμούς SCADA."""

    def __init__(self) -> None:
        self._last_state: int | None = None
        self._voc_base: float | None = None
        self._last_ts: Dict[str, int] = {}

    def _cooldown_ok(self, code: str, ts: int, ms: int = 3000) -> bool:
        if ts - self._last_ts.get(code, -999999) >= ms: # Αποφεύγει να χτυπάει 20 φορές/sec
            self._last_ts[code] = ts
            return True
        return False

    def evaluate(self, pkt: Dict[str, float]) -> List[ScadaAlarm]:
        alarms: List[ScadaAlarm] = []
        ts, state = int(pkt.get("timestamp_ms", 0)), int(pkt.get("state", 0))

        if self._last_state is not None and state != self._last_state: # Αλλαγή φάσης πτήσης
            alarms.append(ScadaAlarm(ts, "INFO", "STATE", f"Mission Phase -> STATE {state}"))
        self._last_state = state

        cell_v = float(pkt.get("batt_v", 0.0)) / BATTERY_CELLS        # Τάση ανά κυψέλη 4S
        if 0.5 < cell_v <= CELL_V_CRIT and self._cooldown_ok("BATT_CRIT", ts):
            alarms.append(ScadaAlarm(ts, "CRIT", "BATT_CRIT", f"CRITICAL Battery Cell: {cell_v:.2f}V!"))
        elif CELL_V_CRIT < cell_v <= CELL_V_WARN and self._cooldown_ok("BATT_WARN", ts):
            alarms.append(ScadaAlarm(ts, "WARN", "BATT_WARN", f"Low Battery Cell: {cell_v:.2f}V"))

        if int(pkt.get("lq_pct", 100)) < 75 and self._cooldown_ok("LOW_LQ", ts):
            alarms.append(ScadaAlarm(ts, "WARN", "LOW_LQ", f"ELRS Signal Low: {int(pkt['lq_pct'])}%"))

        ok, warns = validate_live_packet(pkt)                         # Έλεγχος ορίων αισθητήρων
        for w in ([] if ok else warns):
            if self._cooldown_ok(w, ts):
                alarms.append(ScadaAlarm(ts, "WARN", w, f"Sensor check failed: {w}"))

        voc = float(pkt.get("voc_r2_ohm", 0.0))                       # Έλεγχος απότομης διαρροής VOC
        if voc > 1000:
            if self._voc_base is None:
                self._voc_base = voc
            elif voc < self._voc_base * 0.65 and self._cooldown_ok("VOC_PLUME", ts, 4000):
                alarms.append(ScadaAlarm(ts, "CRIT", "VOC_PLUME", f"VOC Plume Detected! {voc/1000:.1f} kOhm"))
            elif voc > self._voc_base * 0.9:
                self._voc_base = 0.95 * self._voc_base + 0.05 * voc   # Προσαρμογή καθαρού αέρα
        return alarms
