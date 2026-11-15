from dataclasses import dataclass
from typing import Dict, List
from cansat_core.constants import BATTERY_CELLS, CELL_V_CRIT, CELL_V_WARN
from cansat_core import validate_live_packet


@dataclass
class ScadaAlarm:
    timestamp_ms: int
    severity: str
    code: str
    message: str


class ScadaAlarmEngine:
    def __init__(self) -> None:
        self._last_state: int | None = None
        self._voc_baseline: float | None = None
        self._last_alarm_ts: Dict[str, int] = {}

    def _should_emit(self, code: str, ts_ms: int, cooldown_ms: int = 3000) -> bool:
        if ts_ms - self._last_alarm_ts.get(code, -999999) >= cooldown_ms:
            self._last_alarm_ts[code] = ts_ms
            return True
        return False

    def evaluate(self, pkt: Dict[str, float]) -> List[ScadaAlarm]:
        alarms: List[ScadaAlarm] = []
        ts, state = int(pkt.get("timestamp_ms", 0)), int(pkt.get("state", 0))
        if self._last_state is not None and state != self._last_state:
            alarms.append(ScadaAlarm(ts, "INFO", "STATE_CHANGE", f"Transitioned to STATE {state}"))
        self._last_state = state
        cell_v = float(pkt.get("batt_v", 0.0)) / BATTERY_CELLS
        if 0.5 < cell_v <= CELL_V_CRIT and self._should_emit("BATT_CRIT", ts):
            alarms.append(ScadaAlarm(ts, "CRIT", "BATT_CRIT", f"CRITICAL Cell: {cell_v:.2f}V!"))
        elif CELL_V_CRIT < cell_v <= CELL_V_WARN and self._should_emit("BATT_WARN", ts):
            alarms.append(ScadaAlarm(ts, "WARN", "BATT_WARN", f"Low Cell: {cell_v:.2f}V"))
        if int(pkt.get("lq_pct", 100)) < 75 and self._should_emit("LOW_LQ", ts):
            alarms.append(ScadaAlarm(ts, "WARN", "LOW_LQ", f"ELRS LQ low: {int(pkt['lq_pct'])}%"))
        ok, warnings = validate_live_packet(pkt)
        for w in ([] if ok else warnings):
            if self._should_emit(w, ts):
                alarms.append(ScadaAlarm(ts, "WARN", w, f"Validation flag: {w}"))
        voc = float(pkt.get("voc_r2_ohm", 0.0))
        if voc > 1000:
            if self._voc_baseline is None:
                self._voc_baseline = voc
            elif voc < self._voc_baseline * 0.65 and self._should_emit("VOC_PLUME", ts, 4000):
                alarms.append(ScadaAlarm(ts, "CRIT", "VOC_PLUME", f"VOC Anomaly! {voc/1000:.1f} kOhm"))
            elif voc > self._voc_baseline * 0.9:
                self._voc_baseline = 0.95 * self._voc_baseline + 0.05 * voc
        return alarms
