import sqlite3
from pathlib import Path
from typing import Dict


class ScadaHistorianDB:
    """Lightweight SQLite time-series Historian for telemetry & SCADA alarms."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms INTEGER,
                stage INTEGER,
                state INTEGER,
                baro_alt_m REAL,
                press_hpa REAL,
                temp_c REAL,
                hum_pct REAL,
                voc_r2_ohm REAL,
                batt_v REAL,
                curr_a REAL,
                lq_pct INTEGER
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms INTEGER,
                severity TEXT,
                code TEXT,
                message TEXT
            )
        """)
        self.conn.commit()

    def log_telemetry(self, pkt: Dict[str, float], baro_alt_m: float) -> None:
        self.conn.execute(
            """INSERT INTO telemetry
               (timestamp_ms, stage, state, baro_alt_m, press_hpa, temp_c, hum_pct, voc_r2_ohm, batt_v, curr_a, lq_pct)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                int(pkt.get("timestamp_ms", 0)), int(pkt.get("stage", 1)), int(pkt.get("state", 0)),
                float(baro_alt_m), float(pkt.get("press_hpa", 0)), float(pkt.get("temp_c", 0)),
                float(pkt.get("hum_pct", 0)), float(pkt.get("voc_r2_ohm", 0)),
                float(pkt.get("batt_v", 0)), float(pkt.get("curr_a", 0)), int(pkt.get("lq_pct", 0)),
            ),
        )
        self.conn.commit()

    def log_alarm(self, timestamp_ms: int, severity: str, code: str, message: str) -> None:
        self.conn.execute(
            "INSERT INTO alarms (timestamp_ms, severity, code, message) VALUES (?, ?, ?, ?)",
            (int(timestamp_ms), severity, code, message),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
