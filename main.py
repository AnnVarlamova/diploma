import sys
from PySide6.QtWidgets import QApplication
from app import Window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.showMaximized()
    sys.exit(app.exec())
