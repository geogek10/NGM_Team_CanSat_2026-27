#ifndef CANSAT_MISSION_H
#define CANSAT_MISSION_H

#include <stdint.h> // Ακέραιοι σταθερού μεγέθους
#include <stdbool.h> // Τύπος bool

/* Οι 6 αυστηρές καταστάσεις της αποστολής (αντιστοιχούν σε INAV MS_STATE 0-5) */
typedef enum {
    STATE_PRE_LAUNCH         = 0, // Αναμονή στον πύραυλο (μοτέρ κλειδωμένα)
    STATE_LAUNCH             = 1, // Ανίχνευση εκτόξευσης >3.5G (μοτέρ κλειδωμένα)
    STATE_PARACHUTE_DESCENT  = 2, // Κάθοδος με αλεξίπτωτο (μοτέρ κλειδωμένα)
    STATE_TOUCHDOWN_RECOVERY = 3, // Προσγείωση & αναμονή ανάκτησης (μοτέρ κλειδωμένα)
    STATE_GROUND_TRANSFORM   = 4, // Ανάκτηση, άνοιγμα βραχιόνων & ξεκλείδωμα SA
    STATE_DRONE_SCOUT        = 5  // Ενεργή πτήση Drone πάνω από εμπόδια/κρατήρες
} mission_state_t;

/* Κεντρική μνήμη (context) της αποστολής πάνω στον επεξεργαστή STM32G473 */
typedef struct {
    mission_state_t state;       // Τρέχουσα φάση (0-5)
    uint8_t stage;               // 1 = Στάδιο CanSat, 2 = Στάδιο Drone
    bool launch_detected;        // Σημαία ότι έγινε εκτόξευση
    bool motors_arm_permitted;   // ΠΡΟΣΟΧΗ: True ΜΟΝΟ στο Στάδιο 2 (States 4-5)
    uint16_t telemetry_hz;       // 1Hz στην αναμονή, 20Hz στην πτήση
    uint32_t still_timer_ms;     // Χρονόμετρο ακινησίας για επιβεβαίωση προσγείωσης
} mission_ctx_t;

void cansat_mission_init(mission_ctx_t *ctx); // Αρχικοποίηση σε STATE 0 (Ασφαλές)

void cansat_mission_update(
    mission_ctx_t *ctx,  // Δομή κατάστασης αποστολής
    float acc_g,         // Συνολική επιτάχυνση IMU (G)
    float vz_mps,        // Κατακόρυφη ταχύτητα (m/s)
    float alt_m,         // Σχετικό ύψος από το έδαφος (m)
    uint8_t sats,        // Πλήθος δορυφόρων GPS
    bool sa_unlocked,    // Θέση διακόπτη SA στο Boxer (false = κλειδωμένο)
    uint32_t dt_ms       // Χρόνος που πέρασε από τον προηγούμενο έλεγχο (ms)
);

#endif
