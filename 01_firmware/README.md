# 01 — On-Board Firmware (`STM32G473` & `Bluejay ESCs`)
Embedded software running on the **GEPRC GEP-TAKER G4 35A AIO** (`STM32G473 @ 170MHz`).
- `inav_patches/`: Custom C driver (`barometer_bme688.c`) adding BME688 MOX gas-heater sweep (`200C -> 320C -> 400C`) and MAVLink `NAMED_VALUE_FLOAT` telemetry (`VOC_R1`, `VOC_R2`, `HUM_PCT`, `MS_STATE`).
- `inav_configs/`: CLI dumps, Dual-PID profiles, RPM Filter, and 2-Stage Mission State Machine (`STATE 0-5`).
- `bluejay_configs/`: ESC configuration (`48 kHz PWM`, Bi-directional DShot600, `14 poles`, `Demag High`, `DShot Motor Beacon`).
