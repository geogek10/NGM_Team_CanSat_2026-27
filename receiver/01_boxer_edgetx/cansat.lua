-- ============================================================================
-- NGM TEAM CANSAT 2026-27 — CUSTOM EDGETX TELEMETRY HUD (RadioMaster Boxer)
-- Αντιγράψτε αυτό το αρχείο στην κάρτα SD του Boxer: /SCRIPTS/TELEMETRY/cansat.lua
-- Οθόνη Boxer: 128x64 pixels (ασπρόμαυρη)
-- ============================================================================

local lastAlertTime = 0 -- Χρόνος τελευταίας φωνητικής ειδοποίησης (για αποφυγή spam)

-- Βοηθητική συνάρτηση: διαβάζει με ασφάλεια έναν αισθητήρα (αν λείπει, επιστρέφει 0)
local function safeGet(name)
  local val = getValue(name)       -- Ανάγνωση τιμής τηλεμετρίας από το EdgeTX
  if val == nil then return 0 end  -- Αν δεν έχει συνδεθεί ακόμα, επιστροφή 0
  return val
end

-- Εκτελείται 1 φορά όταν ανοίγει η οθόνη τηλεμετρίας
local function init()
  lastAlertTime = getTime()        -- Αποθήκευση αρχικού χρόνου ρολογιού Boxer
end

-- Εκτελείται μόνιμα στο παρασκήνιο (ακόμα κι αν κοιτάς άλλο μενού!)
local function background()
  local rxbt = safeGet("RxBt")     -- Συνολική τάση μπαταρίας 4S (Volts)
  local rqly = safeGet("RQly")     -- Ποιότητα σήματος ELRS Link Quality (%)
  local now  = getTime()           -- Τρέχων χρόνος (σε δεκάδες ms)

  -- Κάθε 5 δευτερόλεπτα (500 * 10ms) ελέγχουμε για κρίσιμους συναγερμούς
  if (now - lastAlertTime) > 500 then
    if rxbt > 5.0 and rxbt < 13.8 then -- Αν η 4S πέσει κάτω από 13.8V (3.45V/cell)
      playTone(880, 200, 50, PLAY_NOW) -- Παίζει προειδοποιητικό ήχο
      playHaptic(20, 0)                -- Δονείται το χειριστήριο στο χέρι!
      lastAlertTime = now
    elseif rqly > 0 and rqly < 75 then -- Αν το σήμα ELRS πέσει κάτω από 75%
      playTone(600, 150, 50, PLAY_NOW) -- Χαμηλός τόνος προειδοποίησης RF
      lastAlertTime = now
    end
  end
end

-- Σχεδιάζει την οθόνη 128x64 (καλείται συνεχώς όταν πατάς το κουμπί TELE)
local function run(event)
  lcd.clear()                          -- Καθαρισμός οθόνης

  -- 1. Ανάγνωση όλων των ζωντανών δεδομένων από ExpressLRS / INAV
  local alt  = safeGet("Alt")          -- Βαρομετρικό υψόμετρο (m)
  local vspd = safeGet("VSpd")         -- Κατακόρυφη ταχύτητα (m/s)
  local batt = safeGet("RxBt")         -- Τάση μπαταρίας 4S (V)
  local curr = safeGet("Curr")         -- Ρεύμα μοτέρ (A)
  local sats = safeGet("Sats")         -- Πλήθος δορυφόρων GPS
  local rqly = safeGet("RQly")         -- Link Quality (%)
  local tmp1 = safeGet("Tmp1")         -- Θερμοκρασία αέρα BME688 (°C)
  local voc  = safeGet("Tmp2")         -- Αντίσταση αερίου VOC (kOhm) από telemetry
  local sa   = safeGet("sa")           -- Θέση διακόπτη ασφαλείας SA (<0 = Κλειδωμένο)

  local cellV = batt / 4.0             -- Υπολογισμός τάσης ανά κυψέλη (4S)
  local armTxt = (sa > 0) and "DRONE:ARM-OK" or "CANSAT:LOCKED" -- Ένδειξη ασφαλείας

  -- 2. Πάνω μπάρα (μαύρη μπάρα με λευκά γράμματα -> INVERS)
  lcd.drawFilledRectangle(0, 0, 128, 11, SOLID)
  lcd.drawText(2, 2, string.format("LQ:%d%%  SAT:%d", rqly, sats), SMLSIZE + INVERS)
  lcd.drawText(76, 2, (sa > 0) and "STAGE2" or "STAGE1", SMLSIZE + INVERS)

  -- 3. Αριστερή στήλη (Πτήση & Ύψος)
  lcd.drawText(2, 14, string.format("ALT: %.1fm", alt), SMLSIZE)
  lcd.drawText(2, 24, string.format("VSp: %.1fm/s", vspd), SMLSIZE)
  lcd.drawText(2, 34, string.format("TMP: %.1fC", tmp1), SMLSIZE)

  -- Κάθετη διαχωριστική γραμμή στη μέση
  lcd.drawLine(64, 12, 64, 50, SOLID, FORCE)

  -- 4. Δεξιά στήλη (Μπαταρία & Αέρια VOC)
  lcd.drawText(68, 14, string.format("BAT:%.1fV", batt), SMLSIZE)
  lcd.drawText(68, 24, string.format("CEL:%.2fV", cellV), SMLSIZE)
  lcd.drawText(68, 34, string.format("VOC:%dkO", voc), SMLSIZE)
  lcd.drawText(68, 44, string.format("CUR:%.1fA", curr), SMLSIZE)

  -- 5. Κάτω μπάρα κατάστασης ασφαλείας SA
  lcd.drawLine(0, 52, 128, 52, SOLID, FORCE)
  local flag = (sa > 0) and (SMLSIZE + INVERS) or SMLSIZE
  lcd.drawText(4, 55, armTxt, flag)
  lcd.drawText(86, 55, "USB-OK", SMLSIZE)
end

return { init = init, background = background, run = run }
