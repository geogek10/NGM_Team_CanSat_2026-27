# 02 — Radio Controller (`RadioMaster Boxer ELRS 2.4GHz`)
EdgeTX telemetry scripts, audio alerts, and switch mappings for the **RadioMaster Boxer (M2)** paired with **RP1/RP2/RP3 V2**.
- **RF Compliance:** ExpressLRS `2.4GHz CE/LBT` at `100mW`, MAVLink bi-directional mode.
- **Laptop Link:** Direct **USB-C Data (EdgeTX USB-VCP Serial Bridge)** — zero extra ESP hardware.
- **HUD (`SCRIPTS/TELEMETRY/cansat.lua`):** 128x64 display for Stage, Altitude, Descent Speed, 4S Cell Voltage, VOCs, Habitability & Sats.
- **Switches (`MODELS/cansat_boxer.yml`):** `SA` Master Lock, `SB` Drone Modes, `SC` Nav Override, `SD` Beacon/Marker, `6-POS` Quick Commands.
