from PyQt6 import QtGui
from PyQt6.QtWidgets import QMainWindow

from interface import style
from interface.views.index import TabsWidget
from state import state


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "YIG filter manager"
        self.setWindowIcon(QtGui.QIcon(f"{state.BASE_DIR}/assets/logo_small.ico"))
        self.setStyleSheet(style.GLOBAL_STYLE)
        self.left = 0
        self.top = 0
        self.width = 400
        self.height = 300
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = TabsWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()
