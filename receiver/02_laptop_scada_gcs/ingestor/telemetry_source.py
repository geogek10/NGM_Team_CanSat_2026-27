import math, random, time
from PySide6.QtCore import QThread, Signal
from pymavlink import mavutil


class BuiltinDemoWorker(QThread):
    """Ενσωματωμένος live προσομοιωτής (για δοκιμές SCADA χωρίς καλώδιο/drone)."""
    packet_received = Signal(dict)  # Σήμα που στέλνει κάθε νέο πακέτο στο GUI
    status_changed = Signal(str)    # Σήμα ενημέρωσης κατάστασης σύνδεσης

    def __init__(self) -> None:
        super().__init__()
        self._running = True

    def stop(self) -> None:
        self._running = False       # Σταματάει καθαρά το thread

    def run(self) -> None:
        self.status_changed.emit("DEMO STREAM ACTIVE (No Hardware Needed)")
        p0, t_ms = 1005.0, 0
        # Στάδιο 1: Εκτόξευση -> Κάθοδος αλεξιπτώτου, Στάδιο 2: Πτήση Drone πάνω από VOC κρατήρα
        for i in range(180):
            if not self._running: break
            if i < 15: stage, state, h, acc, curr = 1, 1, (i / 14) * 900.0, 4.2, 0.18
            elif i < 95: stage, state, h, acc, curr = 1, 2, 900.0 * (1 - (i - 15) / 79), 1.0, 0.18
            elif i < 105: stage, state, h, acc, curr = 1, 3, 0.0, 1.0, 0.15
            else: stage, state, h, acc, curr = 2, 5, 8.0, 1.05, 14.2 + random.gauss(0, 0.7)

            press = p0 * ((1.0 - h / 44330.0) ** 5.2559) + random.gauss(0, 0.08)
            temp = 22.0 - 0.0065 * h + random.gauss(0, 0.1)
            plume = (130 <= i <= 150)              # Προσομοίωση πηγής VOC στον κρατήρα!
            r2 = (48000.0 if plume else 145000.0) + random.gauss(0, 1000)
            pkt = {
                "timestamp_ms": t_ms, "stage": stage, "state": state,
                "lat": 40.630 + 0.00001 * i, "lon": 22.950 + 0.000015 * i,
                "gps_alt_m": 50.0 + h, "sats": 18, "hdop": 0.85,
                "press_hpa": round(press, 2), "temp_c": round(temp, 2), "hum_pct": 53.0,
                "voc_r1_ohm": round(r2 * 1.25, 1), "voc_r2_ohm": round(r2, 1),
                "roll_deg": round(random.gauss(0, 2.0), 1), "pitch_deg": round(random.gauss(0, 2.0), 1),
                "yaw_deg": float((i * 5) % 360), "acc_g": round(acc, 2),
                "batt_v": round(16.6 - 0.008 * i, 2), "curr_a": round(curr, 2), "lq_pct": 99,
            }
            self.packet_received.emit(pkt)         # Αποστολή στο γραφικό παράθυρο
            t_ms += 250
            time.sleep(0.08)                       # Γρήγορη ροή (12.5 πακέτα/sec)
        self.status_changed.emit("DEMO FINISHED")


class UsbMavlinkWorker(QThread):
    """Διαβάζει αληθινά πακέτα MAVLink από το καλώδιο USB-C του Boxer (χωρίς ESP)."""
    packet_received = Signal(dict)
    status_changed = Signal(str)

    def __init__(self, port: str = "/dev/ttyACM0", baud: int = 115200) -> None:
        super().__init__()
        self.port, self.baud = port, baud
        self._running, self._conn = True, None

    def stop(self) -> None:
        self._running = False

    def send_qfe_zero(self) -> None:
        """Στέλνει εντολή SCADA πίσω στο CanSat για μηδενισμό βαρομέτρου."""
        if self._conn is not None:
            self._conn.mav.command_long_send(
                self._conn.target_system, self._conn.target_component,
                mavutil.mavlink.MAV_CMD_PREFLIGHT_CALIBRATION, 0, 0, 0, 1, 0, 0, 0, 0
            )

    def run(self) -> None:
        self.status_changed.emit(f"Connecting USB-C ({self.port})...")
        try:
            self._conn = mavutil.mavlink_connection(self.port, baud=self.baud) # Άνοιγμα σειριακής
        except Exception as exc:
            self.status_changed.emit(f"USB-C Error: {exc}")
            return
        self.status_changed.emit(f"LIVE USB-C CONNECTED: {self.port}")
        latest = {k: 0.0 for k in ["timestamp_ms","lat","lon","gps_alt_m","hdop","roll_deg","pitch_deg","yaw_deg","curr_a"]}
        latest.update({"stage": 1, "state": 0, "sats": 0, "press_hpa": 1013.25, "temp_c": 20.0,
                       "hum_pct": 50.0, "voc_r1_ohm": 150000.0, "voc_r2_ohm": 150000.0,
                       "acc_g": 1.0, "batt_v": 16.0, "lq_pct": 100})
        t0 = time.monotonic()
        while self._running:
            msg = self._conn.recv_match(blocking=True, timeout=0.5) # Αναμονή πακέτου MAVLink
            if msg is None: continue
            mtype = msg.get_type()
            latest["timestamp_ms"] = int((time.monotonic() - t0) * 1000)
            if mtype == "SCALED_PRESSURE":
                latest["press_hpa"], latest["temp_c"] = float(msg.press_abs), float(msg.temperature) / 100.0
                self.packet_received.emit(dict(latest))    # Εκπομπή πλήρους γραμμής στο GUI
            elif mtype == "GLOBAL_POSITION_INT":
                latest["lat"], latest["lon"], latest["gps_alt_m"] = msg.lat / 1e7, msg.lon / 1e7, msg.alt / 1000.0
            elif mtype == "GPS_RAW_INT":
                latest["sats"], latest["hdop"] = int(msg.satellites_visible), msg.eph / 100.0
            elif mtype == "SYS_STATUS":
                latest["batt_v"], latest["curr_a"] = msg.voltage_battery / 1000.0, max(0.0, msg.current_battery / 100.0)
            elif mtype == "NAMED_VALUE_FLOAT":
                name = msg.name.strip("\x00")              # Ανάγνωση custom πεδίων από INAV
                if name == "VOC_R1": latest["voc_r1_ohm"] = float(msg.value)
                elif name == "VOC_R2": latest["voc_r2_ohm"] = float(msg.value)
                elif name == "HUM_PCT": latest["hum_pct"] = float(msg.value)
                elif name == "MS_STATE":
                    latest["state"] = int(msg.value)
                    latest["stage"] = 2 if latest["state"] >= 4 else 1
