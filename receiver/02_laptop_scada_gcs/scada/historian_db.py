import sqlite3
from pathlib import Path
from typing import Dict


class ScadaHistorianDB:
    """Τοπική βάση δεδομένων SQLite που κρατάει ιστορικό τηλεμετρίας & συναγερμών."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp_ms INTEGER, stage INTEGER,
            state INTEGER, baro_alt_m REAL, press_hpa REAL, temp_c REAL,
            voc_r2_ohm REAL, batt_v REAL, curr_a REAL, lq_pct INTEGER)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp_ms INTEGER,
            severity TEXT, code TEXT, message TEXT)""")
        self.conn.commit()

    def log_telemetry(self, pkt: Dict[str, float], alt_m: float) -> None:
        self.conn.execute(
            "INSERT INTO telemetry (timestamp_ms,stage,state,baro_alt_m,press_hpa,temp_c,voc_r2_ohm,batt_v,curr_a,lq_pct) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (int(pkt["timestamp_ms"]), int(pkt["stage"]), int(pkt["state"]), float(alt_m),
             float(pkt["press_hpa"]), float(pkt["temp_c"]), float(pkt["voc_r2_ohm"]),
             float(pkt["batt_v"]), float(pkt["curr_a"]), int(pkt["lq_pct"])))
        self.conn.commit()

    def log_alarm(self, ts: int, sev: str, code: str, msg: str) -> None:
        self.conn.execute("INSERT INTO alarms (timestamp_ms,severity,code,message) VALUES (?,?,?,?)", (ts, sev, code, msg))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
