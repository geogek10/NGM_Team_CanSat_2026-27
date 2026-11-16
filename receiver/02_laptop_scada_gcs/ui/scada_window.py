from collections import deque
from pathlib import Path
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton, QVBoxLayout, QWidget,
)
from core.cansat_physics import STATE_NAMES, compute_isa_altitude
from ingestor.atomic_logger import AtomicMissionLogger
from ingestor.telemetry_source import BuiltinDemoWorker, UsbMavlinkWorker
from scada.alarm_engine import ScadaAlarmEngine
from scada.historian_db import ScadaHistorianDB

pg.setConfigOptions(antialias=True, background="#0f172a", foreground="#e2e8f0")


class FieldScadaWindow(QMainWindow):
    """Κεντρικό παράθυρο ελέγχου SCADA & Live 60FPS γραφημάτων στο πεδίο."""

    def __init__(self, app_dir: Path) -> None:
        super().__init__()
        self.setWindowTitle("NGM Team CanSat — Field SCADA & Live Plots (USB-C)")
        self.resize(1280, 760)
        self.setStyleSheet("background-color:#0b1120; color:#e2e8f0; font-family:sans-serif;")
        self.p0_hpa: float | None = None
        self.worker = None
        self.logger = AtomicMissionLogger(app_dir / "logs")
        self.historian = ScadaHistorianDB(app_dir / "logs" / "scada_historian.db")
        self.alarm_engine = ScadaAlarmEngine()
        for b in ("t", "alt", "temp", "press", "voc", "batt", "curr"):
            setattr(self, f"buf_{b}", deque(maxlen=250))  # Κυλιόμενη μνήμη 250 σημείων
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Πάνω μπάρα επιλογής πηγής & ελέγχου
        top = QHBoxLayout()
        self.src = QComboBox()
        self.src.addItems(["Built-in Live Demo (2-Stage)", "Live USB-C: RadioMaster Boxer"])
        self.port_in = QLineEdit("/dev/ttyACM0")
        self.port_in.setFixedWidth(120)
        self.btn_start = QPushButton("▶ Start Telemetry")
        self.btn_start.setStyleSheet("background:#16a34a; color:white; padding:6px 14px; font-weight:bold;")
        self.btn_start.clicked.connect(self._toggle)
        self.btn_qfe = QPushButton("⌖ Set QFE Zero")
        self.btn_qfe.setStyleSheet("background:#2563eb; color:white; padding:6px 12px;")
        self.btn_qfe.clicked.connect(self._qfe_zero)
        self.lbl_status = QLabel("IDLE")
        self.lbl_phase = QLabel("STAGE 1 | PRE_LAUNCH")
        self.lbl_phase.setStyleSheet("background:#1e293b; color:#38bdf8; padding:6px 12px; font-weight:bold;")
        for w in (QLabel("Source:"), self.src, QLabel("Port:"), self.port_in, self.btn_start, self.btn_qfe, self.lbl_status):
            top.addWidget(w)
        top.addStretch()
        top.addWidget(self.lbl_phase)
        root.addLayout(top)
        # Κύριο σώμα: Αριστερά SCADA HMI + Δεξιά 4 Live Plots
        body = QHBoxLayout()
        left_w = QWidget()
        left_w.setFixedWidth(330)
        left = QVBoxLayout(left_w)

        kpi_box = QGroupBox("SCADA Live Metrics (HMI)")
        grid = QGridLayout(kpi_box)
        self.kpis = {}
        for i, (k, name) in enumerate([("alt","Alt AGL (m)"),("temp","Temp (°C)"),("press","Press (hPa)"),("voc","VOC R2 (kΩ)"),
                                       ("batt","4S Batt (V)"),("curr","Current (A)"),("sats","GNSS Sats"),("lq","ELRS LQ (%)")]):
            r, c = divmod(i, 2)
            grid.addWidget(QLabel(name), r * 2, c)
            val = QLabel("--")
            val.setStyleSheet("font-size:16px; font-weight:bold; color:#38bdf8;")
            grid.addWidget(val, r * 2 + 1, c)
            self.kpis[k] = val
        left.addWidget(kpi_box)

        al_box = QGroupBox("SCADA Alarms & Events")
        al_lay = QVBoxLayout(al_box)
        self.alarm_list = QListWidget()
        self.alarm_list.setStyleSheet("background:#020617; font-size:12px;")
        al_lay.addWidget(self.alarm_list)
        left.addWidget(al_box)
        body.addWidget(left_w)

        pg_grid = QGridLayout()
        self.p_alt = pg.PlotWidget(title="Altitude AGL (m)")
        self.c_alt = self.p_alt.plot(pen=pg.mkPen("#38bdf8", width=2))
        self.p_tmp = pg.PlotWidget(title="Temperature (°C)")
        self.c_tmp = self.p_tmp.plot(pen=pg.mkPen("#fb923c", width=2))
        self.p_voc = pg.PlotWidget(title="BME688 VOC Resistance (kΩ)")
        self.c_voc = self.p_voc.plot(pen=pg.mkPen("#4ade80", width=2))
        self.p_pwr = pg.PlotWidget(title="Battery (V) & Current (A)")
        self.c_bat = self.p_pwr.plot(pen=pg.mkPen("#facc15", width=2))
        self.c_cur = self.p_pwr.plot(pen=pg.mkPen("#f43f5e", width=2))
        pg_grid.addWidget(self.p_alt, 0, 0); pg_grid.addWidget(self.p_tmp, 0, 1)
        pg_grid.addWidget(self.p_voc, 1, 0); pg_grid.addWidget(self.p_pwr, 1, 1)
        body.addLayout(pg_grid)
        root.addLayout(body)

    def _toggle(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop(); self.worker.wait()
            self.btn_start.setText("▶ Start Telemetry")
            self.btn_start.setStyleSheet("background:#16a34a; color:white; padding:6px 14px; font-weight:bold;")
            return
        self.p0_hpa = None
        self.worker = BuiltinDemoWorker() if self.src.currentIndex() == 0 else UsbMavlinkWorker(self.port_in.text().strip())
        self.worker.packet_received.connect(self._on_pkt)
        self.worker.status_changed.connect(self.lbl_status.setText)
        self.worker.start()
        self.btn_start.setText("■ Stop")
        self.btn_start.setStyleSheet("background:#dc2626; color:white; padding:6px 14px; font-weight:bold;")

    def _qfe_zero(self) -> None:
        if self.buf_press:
            self.p0_hpa = self.buf_press[-1]
            self._add_alarm("INFO", f"QFE Zero set to {self.p0_hpa:.2f} hPa")
        if isinstance(self.worker, UsbMavlinkWorker):
            self.worker.send_qfe_zero()

    def _add_alarm(self, sev: str, txt: str) -> None:
        it = QListWidgetItem(f"[{sev}] {txt}")
        it.setForeground(pg.mkColor({"CRIT":"#ef4444","WARN":"#f59e0b","INFO":"#38bdf8"}.get(sev,"#e2e8f0")))
        self.alarm_list.insertItem(0, it)

    def _on_pkt(self, pkt: dict) -> None:
        if self.p0_hpa is None: self.p0_hpa = float(pkt["press_hpa"])
        alt = compute_isa_altitude(float(pkt["press_hpa"]), self.p0_hpa)
        self.logger.log_packet(pkt)                    # Άμεσο σώσιμο στο stage1/stage2 CSV
        self.historian.log_telemetry(pkt, alt)         # Εγγραφή στη SQLite SCADA βάση
        for al in self.alarm_engine.evaluate(pkt):     # Έλεγχος συναγερμών SCADA
            self.historian.log_alarm(al.timestamp_ms, al.severity, al.code, al.message)
            self._add_alarm(al.severity, f"t={al.timestamp_ms/1000:.1f}s | {al.message}")
        self.lbl_phase.setText(f"STAGE {int(pkt['stage'])} | {STATE_NAMES.get(int(pkt['state']), '?')}")
        for k, v in [("alt",f"{alt:.1f}"),("temp",f"{pkt['temp_c']:.1f}"),("press",f"{pkt['press_hpa']:.1f}"),
                     ("voc",f"{pkt['voc_r2_ohm']/1000:.1f}"),("batt",f"{pkt['batt_v']:.2f}"),("curr",f"{pkt['curr_a']:.1f}"),
                     ("sats",f"{int(pkt['sats'])}"),("lq",f"{int(pkt['lq_pct'])}")]:
            self.kpis[k].setText(v)
        self.buf_t.append(pkt["timestamp_ms"]/1000.0); self.buf_alt.append(alt); self.buf_temp.append(pkt["temp_c"])
        self.buf_press.append(pkt["press_hpa"]); self.buf_voc.append(pkt["voc_r2_ohm"]/1000.0)
        self.buf_batt.append(pkt["batt_v"]); self.buf_curr.append(pkt["curr_a"])
        x = list(self.buf_t)
        self.c_alt.setData(x, list(self.buf_alt)); self.c_tmp.setData(x, list(self.buf_temp))
        self.c_voc.setData(x, list(self.buf_voc)); self.c_bat.setData(x, list(self.buf_batt))
        self.c_cur.setData(x, list(self.buf_curr))

    def closeEvent(self, ev) -> None:
        if self.worker and self.worker.isRunning(): self.worker.stop(); self.worker.wait()
        self.logger.close(); self.historian.close(); ev.accept()
