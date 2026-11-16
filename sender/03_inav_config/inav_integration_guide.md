# Οδηγός Ενσωμάτωσης του Custom Κώδικα μέσα στο INAV (STM32G473)

1. Κατεβάστε τον πηγαίο κώδικα του INAV από το GitHub (`git clone https://github.com/iNavFlight/inav.git`).
2. Αντιγράψτε τα αρχεία του `01_bme688_driver/` στον φάκελο `src/main/drivers/barometer/` του INAV.
3. Συνδέστε τις I2C συναρτήσεις του INAV (`busReadRegisterBuffer` / `busWriteRegister`) με το `cansat_bme688_init(...)`.
4. Στο αρχείο `src/main/telemetry/mavlink.c`, στείλτε τα πεδία `voc_r1_ohm`, `voc_r2_ohm`, `hum_pct` και `ctx.state` ως `NAMED_VALUE_FLOAT` (`"VOC_R1"`, `"VOC_R2"`, `"HUM_PCT"`, `"MS_STATE"`).
5. Κάντε compile με `arm-none-eabi-gcc` για το target `GEPRC_TAKER_G4` (STM32G473) και φλασάρετε μέσω `INAV Configurator`.
