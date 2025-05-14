import sys
import os
# Voeg het hoofdproject toe aan het pad
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from gui.views.main_window import MainWindow

# Voeg src toe aan het Python pad (waardoor modules onder src bereikbaar worden)
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Added {src_path} to sys.path")

def load_stylesheet(file_path):
    """Laad de stylesheet voor de applicatie."""
    file = QFile(file_path)
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        return stylesheet
    return ""

print("Starting application...")

if __name__ == "__main__":
    print("Creating QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Grid Simulatie Controller")
    
    # Laad optionele stylesheet
    stylesheet_path = os.path.join(os.path.dirname(__file__), "resources", "styles.qss")
    try:
        stylesheet = load_stylesheet(stylesheet_path)
        if stylesheet:
            app.setStyleSheet(stylesheet)
    except Exception as e:
        print(f"Kon stylesheet niet laden: {e}")
    
    print("Creating main window...")
    window = MainWindow()
    print("Showing main window...")
    window.show()
    print("Starting event loop...")
    
    sys.exit(app.exec())