import time
from pathlib import Path
import pandas as pd
from PySide6.QtCore import QThread, Signal
from pymavlink import mavutil


class CsvReplayWorker(QThread):
    packet_received = Signal(dict)
    status_changed = Signal(str)

    def __init__(self, csv_path: Path, speed_multiplier: float = 4.0) -> None:
        super().__init__()
        self.csv_path = csv_path
        self.speed = max(0.5, speed_multiplier)
        self._running = True

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        if not self.csv_path.exists():
            self.status_changed.emit(f"File not found: {self.csv_path}")
            return
        df = pd.read_csv(self.csv_path)
        self.status_changed.emit(f"REPLAY ACTIVE ({self.speed}x) - {self.csv_path.name}")
        prev_ts = None
        for row in df.to_dict(orient="records"):
            if not self._running:
                break
            ts = int(row.get("timestamp_ms", 0))
            if prev_ts is not None and ts > prev_ts:
                time.sleep(min(((ts - prev_ts) / 1000.0) / self.speed, 0.5))
            prev_ts = ts
            self.packet_received.emit(row)
        self.status_changed.emit("REPLAY FINISHED")


class UsbMavlinkWorker(QThread):
    packet_received = Signal(dict)
    status_changed = Signal(str)

    def __init__(self, port: str = "/dev/ttyACM0", baud: int = 115200) -> None:
        super().__init__()
        self.port = port
        self.baud = baud
        self._running = True
        self._conn = None

    def stop(self) -> None:
        self._running = False

    def send_qfe_zero(self) -> None:
        if self._conn is not None:
            self._conn.mav.command_long_send(
                self._conn.target_system, self._conn.target_component,
                mavutil.mavlink.MAV_CMD_PREFLIGHT_CALIBRATION, 0, 0, 0, 1, 0, 0, 0, 0
            )

    def run(self) -> None:
        self.status_changed.emit(f"Connecting to Boxer USB-C ({self.port})...")
        try:
            self._conn = mavutil.mavlink_connection(self.port, baud=self.baud)
        except Exception as exc:
            self.status_changed.emit(f"USB-C Connection Failed: {exc}")
            return
        self.status_changed.emit(f"CONNECTED LIVE: {self.port}")
        latest = {
            "timestamp_ms": 0, "stage": 1, "state": 0, "lat": 0.0, "lon": 0.0,
            "gps_alt_m": 0.0, "sats": 0, "hdop": 9.9, "press_hpa": 1013.25,
            "temp_c": 20.0, "hum_pct": 50.0, "voc_r1_ohm": 150000.0,
            "voc_r2_ohm": 150000.0, "roll_deg": 0.0, "pitch_deg": 0.0,
            "yaw_deg": 0.0, "acc_g": 1.0, "batt_v": 16.0, "curr_a": 0.2, "lq_pct": 100,
        }
        start_t = time.monotonic()
        while self._running:
            msg = self._conn.recv_match(blocking=True, timeout=0.5)
            if msg is None:
                continue
            mtype = msg.get_type()
            latest["timestamp_ms"] = int((time.monotonic() - start_t) * 1000)
            if mtype == "SCALED_PRESSURE":
                latest["press_hpa"] = float(msg.press_abs)
                latest["temp_c"] = float(msg.temperature) / 100.0
                self.packet_received.emit(dict(latest))
            elif mtype == "GLOBAL_POSITION_INT":
                latest["lat"], latest["lon"] = msg.lat / 1e7, msg.lon / 1e7
                latest["gps_alt_m"] = msg.alt / 1000.0
                latest["yaw_deg"] = (msg.hdg / 100.0) if msg.hdg != 65535 else latest["yaw_deg"]
            elif mtype == "GPS_RAW_INT":
                latest["sats"], latest["hdop"] = int(msg.satellites_visible), msg.eph / 100.0
            elif mtype == "SYS_STATUS":
                latest["batt_v"] = msg.voltage_battery / 1000.0
                latest["curr_a"] = max(0.0, msg.current_battery / 100.0)
            elif mtype == "ATTITUDE":
                latest["roll_deg"], latest["pitch_deg"] = msg.roll * 57.2958, msg.pitch * 57.2958
            elif mtype == "NAMED_VALUE_FLOAT":
                name = msg.name.strip("\x00")
                if name == "VOC_R1": latest["voc_r1_ohm"] = float(msg.value)
                elif name == "VOC_R2": latest["voc_r2_ohm"] = float(msg.value)
                elif name == "HUM_PCT": latest["hum_pct"] = float(msg.value)
                elif name == "MS_STATE":
                    latest["state"] = int(msg.value)
                    latest["stage"] = 2 if latest["state"] >= 4 else 1
            elif mtype == "RADIO_STATUS":
                latest["lq_pct"] = int(msg.rssi)
