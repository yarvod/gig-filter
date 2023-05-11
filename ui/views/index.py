from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui.views.measureTabWidget import MeasureTabWidget
from ui.views.setUpTabWidget import SetUpTabWidget


class TabsWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget(self)
        self.tab_setup = SetUpTabWidget(self)
        self.tab_measure = MeasureTabWidget(self)
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab_setup, "Set Up")
        self.tabs.addTab(self.tab_measure, "Measure")

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
