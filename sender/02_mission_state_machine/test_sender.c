#include <stdio.h>
#include "cansat_mission.h"

int main(void) {
    mission_ctx_t m;
    cansat_mission_init(&m); // Ξεκινάμε στο State 0

    // 1. Ακόμα κι αν κατά λάθος ήταν ξεκλείδωτο το SA στον πύραυλο, τα μοτέρ ΜΕΝΟΥΝ κλειδωμένα:
    cansat_mission_update(&m, 4.2f, 20.0f, 50.0f, 12, true, 500);
    printf("Launch -> State=%d | Stage=%d | ArmAllowed=%d\n", m.state, m.stage, m.motors_arm_permitted);

    // 2. Κάθοδος με αλεξίπτωτο:
    cansat_mission_update(&m, 1.0f, -8.5f, 400.0f, 18, true, 500);
    printf("Descent -> State=%d | Stage=%d | ArmAllowed=%d\n", m.state, m.stage, m.motors_arm_permitted);

    // 3. Προσγείωση (ακινησία 3.5 sec):
    cansat_mission_update(&m, 1.0f, 0.0f, 0.5f, 18, false, 3500);
    printf("Touchdown -> State=%d | Stage=%d | ArmAllowed=%d\n", m.state, m.stage, m.motors_arm_permitted);

    // 4. Ανάκτηση, άνοιγμα βραχιόνων & πάτημα SA από την ομάδα -> Drone Mode!
    cansat_mission_update(&m, 1.0f, 0.0f, 0.2f, 18, true, 500);
    cansat_mission_update(&m, 1.0f, 0.0f, 0.2f, 18, true, 500);
    printf("Drone Ready -> State=%d | Stage=%d | ArmAllowed=%d\n", m.state, m.stage, m.motors_arm_permitted);
    return 0;
}
