import logging
import time

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
from scipy.optimize import curve_fit

from api.keithley_power_supply import KeithleyBlock
from api.rs_fsek30 import SpectrumBlock
from config import config
from ui.windows.calibrationGraphWindow import CalibrationGraphWindow

logger = logging.getLogger(__name__)


class CalibrateWorker(QObject):
    finished = pyqtSignal()
    results = pyqtSignal(dict)
    stream_result = pyqtSignal(dict)

    def run(self):
        dc_block = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        s_block = SpectrumBlock(address=config.SPECTRUM_ADDRESS)

        results = {
            "current_set": [],
            "current_get": [],
            "voltage_get": [],
            "power": [],
            "freq": [],
        }
        current_range = np.linspace(
            config.KEITHLEY_CURRENT_FROM,
            config.KEITHLEY_CURRENT_TO,
            int(config.KEITHLEY_CURRENT_POINTS),
        )

        initial_current = dc_block.get_setted_current()

        for step, current in enumerate(current_range, 1):
            if not config.CALIBRATION_MEAS:
                break
            dc_block.set_current(current)
            if step == 1:
                time.sleep(0.5)
            current_get = dc_block.get_current()
            voltage_get = dc_block.get_voltage()
            s_block.peak_search()
            time.sleep(0.1)
            power = s_block.get_peak_power()
            freq = s_block.get_peak_freq()
            results["current_set"].append(current)
            results["current_get"].append(current_get)
            results["voltage_get"].append(voltage_get)
            results["power"].append(power)
            results["freq"].append(freq)

            self.stream_result.emit(
                {
                    "x": [current_get],
                    "y": [freq],
                    "new_plot": step == 1,
                }
            )

            proc = round(step / config.KEITHLEY_CURRENT_POINTS * 100, 2)
            logger.info(f"[{proc} %]")

        dc_block.set_current(initial_current)

        self.results.emit(results)
        self.finished.emit()


class CalibrationTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.calibrationGraphWindow = None
        self.createGroupCalibration()
        self.layout.addWidget(self.groupCalibration)
        self.setLayout(self.layout)

    def createGroupCalibration(self):
        self.groupCalibration = QGroupBox("Calibration params")
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

        self.btnStartMeas = QPushButton("Start Calibration")
        self.btnStartMeas.clicked.connect(self.start_calibration)

        self.btnStopMeas = QPushButton("Stop Calibration")
        self.btnStopMeas.clicked.connect(self.stop_calibration)

        layout.addWidget(self.keithleyCurrentFromLabel, 1, 0)
        layout.addWidget(self.keithleyCurrentFrom, 1, 1)
        layout.addWidget(self.keithleyCurrentToLabel, 2, 0)
        layout.addWidget(self.keithleyCurrentTo, 2, 1)
        layout.addWidget(self.keithleyCurrentPointsLabel, 3, 0)
        layout.addWidget(self.keithleyCurrentPoints, 3, 1)
        layout.addWidget(self.btnStartMeas, 4, 0, 1, 2)
        layout.addWidget(self.btnStopMeas, 5, 0, 1, 2)

        self.groupCalibration.setLayout(layout)

    def start_calibration(self):
        self.calibration_thread = QThread()
        self.calibration_worker = CalibrateWorker()
        self.calibration_worker.moveToThread(self.calibration_thread)

        config.CALIBRATION_MEAS = True
        config.KEITHLEY_CURRENT_FROM = self.keithleyCurrentFrom.value()
        config.KEITHLEY_CURRENT_TO = self.keithleyCurrentTo.value()
        config.KEITHLEY_CURRENT_POINTS = self.keithleyCurrentPoints.value()

        self.calibration_thread.started.connect(self.calibration_worker.run)
        self.calibration_worker.finished.connect(self.calibration_thread.quit)
        self.calibration_worker.finished.connect(self.calibration_worker.deleteLater)
        self.calibration_thread.finished.connect(self.calibration_thread.deleteLater)
        self.calibration_worker.stream_result.connect(self.show_calibration_graph_window)
        self.calibration_worker.results.connect(self.save_calibration)
        self.calibration_thread.start()

        self.btnStartMeas.setEnabled(False)
        self.calibration_thread.finished.connect(lambda: self.btnStartMeas.setEnabled(True))

        self.btnStopMeas.setEnabled(True)
        self.calibration_thread.finished.connect(lambda: self.btnStopMeas.setEnabled(False))

    def stop_calibration(self):
        config.CALIBRATION_MEAS = False

    def save_calibration(self, results: dict):
        fun = lambda x, a, b: a * x + b
        opt_1, cov_1 = curve_fit(fun, results['freq'], results['current_get'])
        opt_2, cov_2 = curve_fit(fun, results['current_get'], results['freq'])
        config.CALIBRATION_FREQ_2_CURR = list(opt_1)
        config.CALIBRATION_CURR_2_FREQ = list(opt_2)
        try:
            filepath = QFileDialog.getSaveFileName(caption="Save calibration file")[0]
            df = pd.DataFrame(results)
            df.to_csv(filepath)
        except (IndexError, FileNotFoundError):
            pass

    def show_calibration_graph_window(self, results: dict):
        if self.calibrationGraphWindow is None:
            self.calibrationGraphWindow = CalibrationGraphWindow()
        self.calibrationGraphWindow.plotNew(
            x=results.get("x", []),
            y=results.get("y", []),
            new_plot=results.get("new_plot", True),
        )
        self.calibrationGraphWindow.show()
