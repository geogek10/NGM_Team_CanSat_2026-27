# 03 — Shared Core (`cansat_core`)
Reusable Python package acting as the Single Source of Truth across Field SCADA (`04_`), AI (`05_`), Web Backend (`06_`), and Simulators (`07_`).
- `constants.py`: Mission states, ISA constants, sensor limits & standardized `CSV_COLUMNS`.
- `physics.py`: ISA barometric altitude (QFE), air density, Savitzky-Golay `Vz` & electrical power.
- `validation.py`: Live packet validation, MAD outlier rejection & Baro vs GPS cross-sensor check.
- `kml_exporter.py`: Exports validated Stage 1 & Stage 2 trajectories to 3D `.kml` for Google Earth Studio.
