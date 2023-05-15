import logging

import numpy as np
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QFileDialog,
)

from api.keithley_power_supply import KeithleyBlock
from api.rs_nrx import NRXBlock
from config import config

logger = logging.getLogger(__name__)


class MeasureWorker(QObject):
    finished = pyqtSignal()
    results = pyqtSignal(dict)

    def run(self):
        keithley = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        nrx = NRXBlock(ip=config.NRX_IP, avg_time=config.NRX_FILTER_TIME)

        results = {
            "current_set": [],
            "current_get": [],
            "voltage_get": [],
            "power": [],
        }
        current_range = np.linspace(
            config.KEITHLEY_CURRENT_FROM,
            config.KEITHLEY_CURRENT_TO,
            int(config.KEITHLEY_CURRENT_POINTS),
        )

        for step, current in enumerate(current_range, 1):
            if not config.KEITHLEY_MEAS:
                break
            keithley.set_current(current)
            results["current_set"].append(current)
            results["current_get"].append(keithley.get_current())
            results["voltage_get"].append(keithley.get_voltage())
            results["power"].append(nrx.meas())

            proc = round(step / config.KEITHLEY_CURRENT_POINTS * 100, 2)
            logger.info(f"[{proc} %]")

        keithley.close()
        nrx.close()
        self.results.emit(results)
        self.finished.emit()


class MeasureTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.createGroupMeas()
        self.layout.addWidget(self.groupMeas)
        self.setLayout(self.layout)

    def createGroupMeas(self):
        self.groupMeas = QGroupBox("Measure params")
        layout = QGridLayout()

        self.keithleyCurrentFromLabel = QLabel("Current from, A")
        self.keithleyCurrentFrom = QDoubleSpinBox(self)
        self.keithleyCurrentFrom.setRange(0, 5)
        self.keithleyCurrentFrom.setValue(config.KEITHLEY_CURRENT_FROM)

        self.keithleyCurrentToLabel = QLabel("Current to, A")
        self.keithleyCurrentTo = QDoubleSpinBox(self)
        self.keithleyCurrentTo.setRange(0, 5)
        self.keithleyCurrentTo.setValue(config.KEITHLEY_CURRENT_TO)

        self.keithleyCurrentPointsLabel = QLabel("Points count")
        self.keithleyCurrentPoints = QDoubleSpinBox(self)
        self.keithleyCurrentPoints.setRange(0, 1001)
        self.keithleyCurrentPoints.setDecimals(0)
        self.keithleyCurrentPoints.setValue(config.KEITHLEY_CURRENT_POINTS)

        self.btnStartMeas = QPushButton("Start Measure")
        self.btnStartMeas.clicked.connect(self.start_meas)

        self.btnStopMeas = QPushButton("Stop Measure")
        self.btnStopMeas.clicked.connect(self.stop_meas)

        layout.addWidget(self.keithleyCurrentFromLabel, 1, 0)
        layout.addWidget(self.keithleyCurrentFrom, 1, 1)
        layout.addWidget(self.keithleyCurrentToLabel, 2, 0)
        layout.addWidget(self.keithleyCurrentTo, 2, 1)
        layout.addWidget(self.keithleyCurrentPointsLabel, 3, 0)
        layout.addWidget(self.keithleyCurrentPoints, 3, 1)
        layout.addWidget(self.btnStartMeas, 4, 0, 1, 2)
        layout.addWidget(self.btnStopMeas, 5, 0, 1, 2)

        self.groupMeas.setLayout(layout)

    def start_meas(self):
        self.meas_thread = QThread()
        self.meas_worker = MeasureWorker()
        self.meas_worker.moveToThread(self.meas_thread)

        config.KEITHLEY_MEAS = True
        config.KEITHLEY_CURRENT_FROM = self.keithleyCurrentFrom.value()
        config.KEITHLEY_CURRENT_TO = self.keithleyCurrentTo.value()
        config.KEITHLEY_CURRENT_POINTS = self.keithleyCurrentPoints.value()

        self.meas_thread.started.connect(self.meas_worker.run)
        self.meas_worker.finished.connect(self.meas_thread.quit)
        self.meas_worker.finished.connect(self.meas_worker.deleteLater)
        self.meas_thread.finished.connect(self.meas_thread.deleteLater)
        self.meas_worker.results.connect(self.save_meas)
        self.meas_thread.start()

        self.btnStartMeas.setEnabled(False)
        self.meas_thread.finished.connect(lambda: self.btnStartMeas.setEnabled(True))

        self.btnStopMeas.setEnabled(True)
        self.meas_thread.finished.connect(lambda: self.btnStopMeas.setEnabled(False))

    def stop_meas(self):
        config.KEITHLEY_MEAS = False

    def save_meas(self, results: dict):
        try:
            filepath = QFileDialog.getSaveFileName()[0]
            df = pd.DataFrame(results)
            df.to_csv(filepath)
        except (IndexError, FileNotFoundError):
            pass
