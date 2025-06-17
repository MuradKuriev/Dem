from PyQt6.QtGui import QIcon

from gui import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('Образ плюс.png'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())