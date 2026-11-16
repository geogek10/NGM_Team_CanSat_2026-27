# `sender/` — Κώδικας & Ρυθμίσεις πάνω στο CanSat / Drone

Περιέχει όλο το ενσωματωμένο λογισμικό για την πλακέτα **GEPRC GEP-TAKER G4 35A AIO (`STM32G473 @ 170MHz`)**:
- `01_bme688_driver/`: Επίσημο Bosch BME68x API + Custom C Driver (`bme688_cansat.c`) με κύκλο θέρμανσης 200°C/350°C για VOCs.
- `02_mission_state_machine/`: Η λογική των 2 σταδίων σε C (`STATE 0–3` κλειδωμένο CanSat → Ανάκτηση → `STATE 4–5` Drone Scout) + πρόγραμμα δοκιμής `test_sender.c`.
- `03_inav_config/`: Όλες οι ρυθμίσεις CLI του INAV με ελληνικά σχόλια & οδηγός ενσωμάτωσης.
- `04_esc_bluejay_elrs/`: Διάγραμμα καλωδίωσης, ρυθμίσεις Bluejay 48kHz (`14P`) & ExpressLRS CE/LBT 100mW.
