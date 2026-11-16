# Ρύθμιση Κουμπιών & USB-C στο RadioMaster Boxer (EdgeTX)

## 1. Προγραμματισμός Κουμπιών (στο μενού MIXES / SPECIAL FUNCTIONS)
- **SA (Αριστερά Πάνω - Latching):** Κλείδωμα Ασφαλείας. *Πάνω* = Μοτέρ ΝΕΚΡΑ (υποχρεωτικό στον πύραυλο & κάθοδο CanSat). *Πατημένο* = Άδεια πτήσης Drone μετά την ανάκτηση.
- **SB (Αριστερά 3-θέσεων):** Modes Drone (*Πάνω* = Auto Waypoint, *Μέση* = Manual Angle, *Κάτω* = PosHold/AltHold).
- **SC (Δεξιά 3-θέσεων):** Πλοήγηση (*Πάνω* = Normal, *Μέση* = Force RTH, *Κάτω* = Auto-Land επιτόπου).
- **SD (Δεξιά Πάνω - Momentary):** Κρατώντας το πατημένο μετά την προσγείωση, ηχεί το **DShot Motor Beacon** (σειρήνα μοτέρ) για εντοπισμό.
- **6-POS (1–6):** 1=QFE Zero, 2=PID Profile 1 (Άνεμος), 3=PID Profile 2 (Απαλή σάρωση), 4=SD Card Log On/Off, 5=Αλλαγή οθόνης, 6=Φωνητική εκφώνηση.
- **S1 / S2:** S1=Ένταση ήχου · S2=Ταχύτητα σάρωσης/καθόδου.

## 2. Σύνδεση με Laptop (Χωρίς ESP!) & Εφεδρικό Log
- **USB-C Σύνδεση:** Στο μενού *Model Setup / Radio Setup → USB Mode* επιλέξτε **`USB Serial (VCP)`** (ή σύνδεση telemetry bridge) ώστε συνδέοντας το καλώδιο USB-C στο Laptop να εμφανίζεται ως θύρα `/dev/ttyACM0`.
- **SD Card Backup:** Στα *Special Functions* προσθέστε: `ON -> SD Logs (1.0s)` για αυτόματη εφεδρική εγγραφή `.csv` στην κάρτα μνήμης του Boxer.
