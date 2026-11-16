#include "cansat_mission.h"

void cansat_mission_init(mission_ctx_t *ctx) {
    ctx->state = STATE_PRE_LAUNCH;     // Ξεκινάμε πάντα σε ασφαλή αναμονή (State 0)
    ctx->stage = 1;                    // Στάδιο 1 (CanSat)
    ctx->launch_detected = false;      // Δεν έχει γίνει ακόμα εκτόξευση
    ctx->motors_arm_permitted = false; // ΚΙΝΗΤΗΡΕΣ ΑΥΣΤΗΡΑ ΚΛΕΙΔΩΜΕΝΟΙ
    ctx->telemetry_hz = 1;             // 1Hz στον πύραυλο για οικονομία μπαταρίας
    ctx->still_timer_ms = 0;           // Μηδενισμός χρονομέτρου προσγείωσης
}

void cansat_mission_update(
    mission_ctx_t *ctx, float acc_g, float vz_mps,
    float alt_m, uint8_t sats, bool sa_unlocked, uint32_t dt_ms
) {
    switch (ctx->state) {
        case STATE_PRE_LAUNCH:
            ctx->motors_arm_permitted = false; // Απαγορεύεται ρητά η όπλιση στον πύραυλο
            if (acc_g > 3.5f && vz_mps > 12.0f) { // Ανίχνευση ισχυρής ανόδου πυραύλου
                ctx->launch_detected = true;      // Σημειώνουμε ότι εκτοξευτήκαμε
                ctx->state = STATE_LAUNCH;        // Μετάβαση σε State 1
                ctx->telemetry_hz = 20;           // Ανεβάζουμε τηλεμετρία στα 20Hz
            }
            break;

        case STATE_LAUNCH:
            ctx->motors_arm_permitted = false;    // Κινητήρες κλειδωμένοι στην άνοδο
            if (ctx->launch_detected && vz_mps < -2.5f) { // Αρχίζει η κάθοδος μετά το Apogee
                ctx->state = STATE_PARACHUTE_DESCENT;     // Μετάβαση σε State 2 (Αλεξίπτωτο)
            }
            break;

        case STATE_PARACHUTE_DESCENT:
            ctx->motors_arm_permitted = false;    // Κινητήρες κλειδωμένοι σε όλη την κάθοδο
            if (alt_m < 3.0f && acc_g > 0.92f && acc_g < 1.08f && vz_mps > -0.5f && vz_mps < 0.5f) {
                ctx->still_timer_ms += dt_ms;     // Μετράμε πόση ώρα είναι ακίνητο στο έδαφος
                if (ctx->still_timer_ms >= 3000) { // Αν μείνει ακίνητο 3 δευτερόλεπτα
                    ctx->state = STATE_TOUCHDOWN_RECOVERY; // Επιβεβαιωμένη προσγείωση!
                    ctx->telemetry_hz = 1;        // Χαμηλός ρυθμός 1Hz για εντοπισμό
                }
            } else {
                ctx->still_timer_ms = 0;          // Μηδενισμός αν κουνηθεί από τον άνεμο
            }
            break;

        case STATE_TOUCHDOWN_RECOVERY:
            ctx->motors_arm_permitted = false;    // Κλειδωμένο μέχρι να το ανακτήσει η ομάδα
            if (sa_unlocked && alt_m < 3.0f) {    // Η ομάδα το πήρε, άνοιξε βραχίονες & πάτησε SA
                ctx->stage = 2;                   // Μετάβαση στο Στάδιο 2 (Πλανητικό Drone!)
                ctx->state = STATE_GROUND_TRANSFORM;
            }
            break;

        case STATE_GROUND_TRANSFORM:
            if (!sa_unlocked) {                   // Αν ξανακλειδωθεί το SA, κλείνουν αμέσως όλα
                ctx->motors_arm_permitted = false;
            } else if (sats >= 8) {               // Έλεγχος ότι έχουμε ≥8 δορυφόρους GPS
                ctx->motors_arm_permitted = true; // ΠΛΕΟΝ ΕΠΙΤΡΕΠΕΤΑΙ Η ΠΤΗΣΗ DRONE!
                ctx->telemetry_hz = 20;           // 20Hz τηλεμετρία για την πτήση
                ctx->state = STATE_DRONE_SCOUT;   // Μετάβαση σε State 5 (Εξερεύνηση)
            }
            break;

        case STATE_DRONE_SCOUT:
            ctx->motors_arm_permitted = sa_unlocked; // Άμεσο Kill-Switch αν κλειδωθεί το SA
            break;
    }
}
