# NGM Team CanSat 2026–27 — Planetary Aerial Scout

Ανοιχτό αποθετήριο λογισμικού για το υβριδικό **Drone-CanSat** της ομάδας NGM.

## Αρχιτεκτονική Συστήματος
1. `01_firmware/` — Custom INAV (STM32G473 @ 170MHz) με BME688 VOC driver & Bluejay ESC configs.
2. `02_radio_controller/` — EdgeTX Lua HUD (`cansat.lua`), φωνητικά alerts & ρυθμίσεις RadioMaster Boxer.
3. `03_shared_core/` — Κοινός Python πυρήνας (`cansat_core`): φυσική ISA, επικύρωση, `.kml` exporter.
4. `04_field_gcs_scada/` — Εφαρμογή πεδίου (USB-C MAVLink, Live 60FPS Plots, SCADA Alarms & Historian).
5. `05_neural_networks/` — Εκπαίδευση 3 Νευρωνικών Δικτύων (`GasSpecNet`, `HabitabilityNet`, `AeroHealthNet`).
6. `06_web_dashboard/` — Full-Stack Web Dashboard (FastAPI + React/ECharts/Deck.gl) & Google Earth Studio export.
7. `07_tools_and_tests/` — Προσομοιωτές πτήσης (για δοκιμές χωρίς hardware) & unit tests.
8. `docs/` — Τεκμηρίωση, διαγράμματα συνδεσμολογίας & αρχιτεκτονική.
