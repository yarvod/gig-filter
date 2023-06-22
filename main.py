import os
import sys

from PyQt6.QtWidgets import QApplication

from interface.index import App
from state import state


state.BASE_DIR = os.path.dirname(__file__)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())
