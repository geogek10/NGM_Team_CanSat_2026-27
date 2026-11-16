#include "bme688_cansat.h"

static uint16_t heater_temps[2] = { 200, 350 }; // Θερμοκρασίες θερμαντήρα MOX σε °C (Βήμα 1 & 2)
static uint16_t heater_durs[2]  = { 100, 100 }; // Διάρκεια θέρμανσης σε ms για κάθε βήμα
static uint8_t s_dev_addr = 0x76;               // Αποθήκευση I2C διεύθυνσης (0x76 ή 0x77)

int8_t cansat_bme688_init(
    struct bme68x_dev *dev,
    uint8_t i2c_addr,
    bme68x_read_fptr_t read_fn,
    bme68x_write_fptr_t write_fn,
    bme68x_delay_us_fptr_t delay_fn
) {
    s_dev_addr = i2c_addr;            // Κρατάμε τη διεύθυνση στη μνήμη
    dev->intf = BME68X_I2C_INTF;      // Ορίζουμε επικοινωνία I2C (όχι SPI)
    dev->intf_ptr = &s_dev_addr;      // Δείκτης προς τη διεύθυνση I2C
    dev->read = read_fn;              // Συνδέουμε τη συνάρτηση ανάγνωσης της πλακέτας
    dev->write = write_fn;            // Συνδέουμε τη συνάρτηση εγγραφής της πλακέτας
    dev->delay_us = delay_fn;         // Συνδέουμε τη συνάρτηση χρονοκαθυστέρησης
    dev->amb_temp = 20;               // Αρχική θερμοκρασία περιβάλλοντος αναφοράς (20°C)

    int8_t rslt = bme68x_init(dev);   // Έλεγχος Chip ID (0x61) & φόρτωση εργοστασιακής βαθμονόμησης
    if (rslt != BME68X_OK) return rslt; // Αν απέτυχε η επικοινωνία I2C, επιστρέφουμε σφάλμα

    struct bme68x_conf conf = {
        .os_hum   = BME68X_OS_2X,       // Δειγματοληψία υγρασίας 2x (καθαρό σήμα)
        .os_press = BME68X_OS_4X,       // Δειγματοληψία πίεσης 4x (υψηλή ακρίβεια υψομέτρου)
        .os_temp  = BME68X_OS_4X,       // Δειγματοληψία θερμοκρασίας 4x
        .filter   = BME68X_FILTER_SIZE_3, // Εσωτερικό φίλτρο IIR κατά του θορύβου ανέμου
        .odr      = BME68X_ODR_NONE     // Χωρίς επιπλέον αναμονή μεταξύ βημάτων
    };
    rslt = bme68x_set_conf(&conf, dev); // Αποστολή ρυθμίσεων στον αισθητήρα
    if (rslt != BME68X_OK) return rslt;

    struct bme68x_heatr_conf heatr = {
        .enable      = BME68X_ENABLE,   // Ενεργοποίηση του θερμαντήρα αερίων VOC
        .temp_prof   = heater_temps,    // Πίνακας θερμοκρασιών [200°C, 350°C]
        .dur_prof    = heater_durs,     // Πίνακας διάρκειας [100ms, 100ms]
        .profile_len = 2                // Πλήθος βημάτων στον κύκλο θέρμανσης
    };
    rslt = bme68x_set_heatr_conf(BME68X_SEQUENTIAL_MODE, &heatr, dev); // Διαδοχικός κύκλος
    if (rslt != BME68X_OK) return rslt;

    return bme68x_set_op_mode(BME68X_SEQUENTIAL_MODE, dev); // Εκκίνηση συνεχούς μέτρησης
}

int8_t cansat_bme688_read_step(struct bme68x_dev *dev, cansat_env_data_t *out) {
    struct bme68x_data data[3];       // Προσωρινός πίνακας για τα δεδομένα των βημάτων
    uint8_t n_fields = 0;             // Πόσες νέες μετρήσεις ήταν έτοιμες

    int8_t rslt = bme68x_get_data(BME68X_SEQUENTIAL_MODE, data, &n_fields, dev);
    if (rslt != BME68X_OK || n_fields == 0) return rslt; // Αν δεν υπάρχει νέο δείγμα, έξοδος

    for (uint8_t i = 0; i < n_fields; i++) {
        if (data[i].status & BME68X_NEW_DATA_MSK) {          // Έλεγχος αν είναι φρέσκια μέτρηση
            out->press_hpa = data[i].pressure / 100.0f;      // Μετατροπή Pascal -> hPa
            out->temp_c    = data[i].temperature;            // Θερμοκρασία σε °C
            out->hum_pct   = data[i].humidity;               // Υγρασία σε %
            out->heater_stable = (data[i].status & BME68X_HEAT_STAB_MSK) != 0; // Σταθερός θερμαντήρας;

            if ((data[i].status & BME68X_GASM_VALID_MSK) && out->heater_stable) {
                if (data[i].gas_index == 0) out->voc_r1_ohm = data[i].gas_resistance; // Τιμή 200°C
                if (data[i].gas_index == 1) out->voc_r2_ohm = data[i].gas_resistance; // Τιμή 350°C
            }
        }
    }
    return BME68X_OK; // Επιτυχής ανάγνωση
}
