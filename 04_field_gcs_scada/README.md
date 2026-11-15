# 04 — Field Ground Control Station & SCADA
Real-time offline laptop software for the launch field.
- `ingestor/`: Reads MAVLink over Boxer **USB-C Serial** and atomically logs `stage1_descent.csv`, `stage2_drone_scout.csv` & `.tlog`.
- `scada/`: HMI health indicators, threshold alarms (`Cell < 3.40V`, `LQ < 70%`, timeouts, VOC spikes), SQLite Historian DB & supervisory commands.
- `ui/`: 60 FPS live plots (`PySide6` + `PyQtGraph`) and 2D GPS map.
