import sys
from pathlib import Path

# This tells Python to look inside the 'src' folder for your modules
src_path = str(Path(__file__).parent.resolve() / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Now we can safely import and run the app
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Clean, modern cross-platform styling
    window = MainWindow()
    window.show()
    sys.exit(app.exec())