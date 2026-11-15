from collections import deque
from pathlib import Path
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QVBoxLayout, QWidget, QGridLayout, QGroupBox,
)
from cansat_core import MissionState, compute_electrical_power, compute_isa_altitude
from ingestor.atomic_logger import AtomicMissionLogger
from ingestor.telemetry_source import CsvReplayWorker, UsbMavlinkWorker
from scada.alarm_engine import ScadaAlarmEngine
from scada.historian_db import ScadaHistorianDB

pg.setConfigOptions(antialias=True, background="#0f172a", foreground="#e2e8f0")
STATE_NAMES = {s.value: s.name for s in MissionState}


class FieldScadaWindow(QMainWindow):
    def __init__(self, repo_root: Path) -> None:
        super().__init__()
        self.repo_root = repo_root
        self.setWindowTitle("NGM Team CanSat 2026-27 — Field SCADA & Live Telemetry")
        self.resize(1280, 780)
        self.setStyleSheet("background-color: #0b1120; color: #e2e8f0; font-family: sans-serif;")
        self.p0_hpa: float | None = None
        self.worker = None
        self.logger = AtomicMissionLogger(repo_root / "04_field_gcs_scada" / "logs")
        self.historian = ScadaHistorianDB(repo_root / "04_field_gcs_scada" / "logs" / "scada_historian.db")
        self.alarm_engine = ScadaAlarmEngine()
        for name in ("buf_t", "buf_alt", "buf_temp", "buf_press", "buf_voc", "buf_batt", "buf_curr"):
            setattr(self, name, deque(maxlen=300))
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        top = QHBoxLayout()
        self.source_box = QComboBox()
        self.source_box.addItems(["Replay: sample_flight.csv (4x)", "Live USB-C: RadioMaster Boxer"])
        self.port_input = QLineEdit("/dev/ttyACM0")
        self.port_input.setFixedWidth(130)
        self.btn_start = QPushButton("▶ Start Telemetry")
        self.btn_start.setStyleSheet("background:#16a34a; color:white; padding:6px 14px; font-weight:bold;")
        self.btn_start.clicked.connect(self._toggle_stream)
        self.btn_qfe = QPushButton("⌖ Set QFE Zero")
        self.btn_qfe.setStyleSheet("background:#2563eb; color:white; padding:6px 12px;")
        self.btn_qfe.clicked.connect(self._calibrate_qfe)
        self.lbl_status = QLabel("IDLE")
        self.lbl_phase = QLabel("STAGE 1 | PRE_LAUNCH")
        self.lbl_phase.setStyleSheet("background:#1e293b; color:#38bdf8; padding:6px 12px; font-weight:bold;")
        for w in (QLabel("Source:"), self.source_box, QLabel("Port:"), self.port_input, self.btn_start, self.btn_qfe, self.lbl_status):
            top.addWidget(w)
        top.addStretch()
        top.addWidget(self.lbl_phase)
        root.addLayout(top)
        body = QHBoxLayout()
        left_w = QWidget()
        left_w.setFixedWidth(340)
        left = QVBoxLayout(left_w)
        kpi_box = QGroupBox("SCADA Live Metrics (HMI)")
        kpi_grid = QGridLayout(kpi_box)
        self.kpis = {}
        fields = [("alt", "Baro Alt (m)"), ("temp", "Temp (C)"), ("press", "Press (hPa)"), ("hum", "Humidity (%)"),
                  ("voc", "VOC R2 (kOhm)"), ("batt", "4S Batt (V)"), ("curr", "Current (A)"), ("pwr", "Power (W)"),
                  ("sats", "GNSS Sats"), ("lq", "ELRS LQ (%)")]
        for i, (k, title) in enumerate(fields):
            r, c = divmod(i, 2)
            kpi_grid.addWidget(QLabel(title), r * 2, c)
            v = QLabel("--")
            v.setStyleSheet("font-size:15px; font-weight:bold; color:#38bdf8;")
            kpi_grid.addWidget(v, r * 2 + 1, c)
            self.kpis[k] = v
        left.addWidget(kpi_box)
        alarm_box = QGroupBox("SCADA Alarms & Events")
        al_lay = QVBoxLayout(alarm_box)
        self.alarm_list = QListWidget()
        self.alarm_list.setStyleSheet("background:#020617; font-size:12px;")
        al_lay.addWidget(self.alarm_list)
        left.addWidget(alarm_box)
        body.addWidget(left_w)

        pg_grid = QGridLayout()
        self.p_alt = pg.PlotWidget(title="Altitude AGL (m)")
        self.c_alt = self.p_alt.plot(pen=pg.mkPen("#38bdf8", width=2))
        self.p_atm = pg.PlotWidget(title="Temperature (C)")
        self.c_temp = self.p_atm.plot(pen=pg.mkPen("#fb923c", width=2))
        self.p_voc = pg.PlotWidget(title="BME688 VOC Resistance (kOhm)")
        self.c_voc = self.p_voc.plot(pen=pg.mkPen("#4ade80", width=2))
        self.p_pwr = pg.PlotWidget(title="4S Voltage (V) & Current (A)")
        self.c_batt = self.p_pwr.plot(pen=pg.mkPen("#facc15", width=2))
        self.c_curr = self.p_pwr.plot(pen=pg.mkPen("#f43f5e", width=2))
        pg_grid.addWidget(self.p_alt, 0, 0)
        pg_grid.addWidget(self.p_atm, 0, 1)
        pg_grid.addWidget(self.p_voc, 1, 0)
        pg_grid.addWidget(self.p_pwr, 1, 1)
        body.addLayout(pg_grid)
        root.addLayout(body)

    def _toggle_stream(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.btn_start.setText("▶ Start Telemetry")
            self.btn_start.setStyleSheet("background:#16a34a; color:white; padding:6px 14px; font-weight:bold;")
            return
        self.p0_hpa = None
        if self.source_box.currentIndex() == 0:
            self.worker = CsvReplayWorker(self.repo_root / "05_neural_networks" / "datasets" / "sample_flight.csv", 4.0)
        else:
            self.worker = UsbMavlinkWorker(port=self.port_input.text().strip())
        self.worker.packet_received.connect(self._on_packet)
        self.worker.status_changed.connect(self.lbl_status.setText)
        self.worker.start()
        self.btn_start.setText("■ Stop")
        self.btn_start.setStyleSheet("background:#dc2626; color:white; padding:6px 14px; font-weight:bold;")

    def _calibrate_qfe(self) -> None:
        if self.buf_press:
            self.p0_hpa = self.buf_press[-1]
            self._add_alarm("INFO", f"QFE calibrated to {self.p0_hpa:.2f} hPa")
        if isinstance(self.worker, UsbMavlinkWorker):
            self.worker.send_qfe_zero()

    def _add_alarm(self, severity: str, text: str) -> None:
        item = QListWidgetItem(f"[{severity}] {text}")
        item.setForeground(pg.mkColor({"CRIT": "#ef4444", "WARN": "#f59e0b", "INFO": "#38bdf8"}.get(severity, "#e2e8f0")))
        self.alarm_list.insertItem(0, item)

    def _on_packet(self, pkt: dict) -> None:
        if self.p0_hpa is None:
            self.p0_hpa = float(pkt.get("press_hpa", 1013.25))
        alt_m = compute_isa_altitude(float(pkt["press_hpa"]), p0_hpa=self.p0_hpa)
        pwr_w = compute_electrical_power(float(pkt["batt_v"]), float(pkt["curr_a"]))
        self.logger.log_packet(pkt)
        self.historian.log_telemetry(pkt, alt_m)
        for al in self.alarm_engine.evaluate(pkt):
            self.historian.log_alarm(al.timestamp_ms, al.severity, al.code, al.message)
            self._add_alarm(al.severity, f"t={al.timestamp_ms/1000:.1f}s | {al.message}")
        self.lbl_phase.setText(f"STAGE {int(pkt.get('stage', 1))} | {STATE_NAMES.get(int(pkt.get('state', 0)), '?')}")
        for k, val in [("alt", f"{alt_m:.1f}"), ("temp", f"{pkt['temp_c']:.1f}"), ("press", f"{pkt['press_hpa']:.1f}"),
                       ("hum", f"{pkt['hum_pct']:.1f}"), ("voc", f"{pkt['voc_r2_ohm']/1000:.1f}"), ("batt", f"{pkt['batt_v']:.2f}"),
                       ("curr", f"{pkt['curr_a']:.1f}"), ("pwr", f"{pwr_w:.0f}"), ("sats", f"{int(pkt['sats'])}"), ("lq", f"{int(pkt['lq_pct'])}")]:
            self.kpis[k].setText(val)
        self.buf_t.append(pkt["timestamp_ms"] / 1000.0)
        self.buf_alt.append(alt_m)
        self.buf_temp.append(pkt["temp_c"] if -40 <= pkt["temp_c"] <= 85 else (self.buf_temp[-1] if self.buf_temp else 20.0))
        self.buf_press.append(pkt["press_hpa"])
        self.buf_voc.append(pkt["voc_r2_ohm"] / 1000.0)
        self.buf_batt.append(pkt["batt_v"])
        self.buf_curr.append(pkt["curr_a"])
        x = list(self.buf_t)
        self.c_alt.setData(x, list(self.buf_alt))
        self.c_temp.setData(x, list(self.buf_temp))
        self.c_voc.setData(x, list(self.buf_voc))
        self.c_batt.setData(x, list(self.buf_batt))
        self.c_curr.setData(x, list(self.buf_curr))

    def closeEvent(self, event) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        self.logger.close()
        self.historian.close()
        event.accept()
