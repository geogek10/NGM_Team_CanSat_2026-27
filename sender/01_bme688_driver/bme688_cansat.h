#ifndef BME688_CANSAT_H
#define BME688_CANSAT_H

#include <stdint.h>           // Τυποποιημένοι ακέραιοι (uint8_t, int8_t κλπ.)
#include <stdbool.h>          // Υποστήριξη λογικού τύπου true / false
#include "bosch_api/bme68x.h" // Επίσημη βιβλιοθήκη της Bosch για το τσιπ BME688

/* Δομή που κρατάει όλες τις μετρήσεις του αισθητήρα περιβάλλοντος BME688 */
typedef struct {
    float press_hpa;      // Ατμοσφαιρική πίεση σε hPa (millibars)
    float temp_c;         // Θερμοκρασία αέρα σε βαθμούς Κελσίου (°C)
    float hum_pct;        // Σχετική υγρασία αέρα (%)
    float voc_r1_ohm;     // Αντίσταση αερίου στους 200°C (ευαίσθητη σε ελαφριά αέρια)
    float voc_r2_ohm;     // Αντίσταση αερίου στους 350°C (ευαίσθητη σε καυσαέρια/VOCs)
    bool heater_stable;   // True μόνο όταν ο θερμαντήρας έπιασε σταθερή θερμοκρασία
} cansat_env_data_t;

/* Αρχικοποίηση του BME688 στον δίαυλο I2C (με κύκλο θέρμανσης 2 βημάτων) */
int8_t cansat_bme688_init(
    struct bme68x_dev *dev,         // Δομή συσκευής Bosch BME68x
    uint8_t i2c_addr,               // Διεύθυνση I2C του αισθητήρα (0x76 ή 0x77)
    bme68x_read_fptr_t read_fn,     // Συνάρτηση ανάγνωσης I2C της πλακέτας (INAV HAL)
    bme68x_write_fptr_t write_fn,   // Συνάρτηση εγγραφής I2C της πλακέτας (INAV HAL)
    bme68x_delay_us_fptr_t delay_fn // Συνάρτηση καθυστέρησης σε microseconds
);

/* Ανάγνωση των τελευταίων μετρήσεων & ενημέρωση της δομής εξόδου */
int8_t cansat_bme688_read_step(struct bme68x_dev *dev, cansat_env_data_t *out);

#endif
