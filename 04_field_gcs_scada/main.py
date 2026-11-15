import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from ui.main_window import FieldScadaWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FieldScadaWindow(Path(__file__).resolve().parents[1])
    win.show()
    sys.exit(app.exec())
