import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from ui.scada_window import FieldScadaWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)                        # Εκκίνηση Qt εφαρμογής
    win = FieldScadaWindow(Path(__file__).resolve().parent) # Άνοιγμα SCADA παραθύρου
    win.show()
    sys.exit(app.exec())
