import logging
import time

import numpy as np
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QFileDialog,
    QSizePolicy,
)

from api.keithley_power_supply import KeithleyBlock
from api.rs_nrx import NRXBlock
from config import config
from ui.windows.measureGraphWindow import MeasureGraphWindow
from utils.functions import linear

logger = logging.getLogger(__name__)


class MeasureWorker(QObject):
    finished = pyqtSignal()
    results = pyqtSignal(dict)
    stream_result = pyqtSignal(dict)

    def run(self):
        keithley = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        nrx = NRXBlock(
            ip=config.NRX_IP,
            filter_time=config.NRX_FILTER_TIME,
            aperture_time=config.NRX_APER_TIME,
        )

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
        start_time = time.time()
        initial_current = keithley.get_setted_current()
        for step, current in enumerate(current_range, 1):
            if not config.KEITHLEY_MEAS:
                break
            keithley.set_current(current)
            time.sleep(0.01)
            if step == 1:
                time.sleep(0.4)
            current_get = keithley.get_current()
            voltage_get = keithley.get_voltage()
            power = nrx.get_power()
            results["current_set"].append(current)
            results["current_get"].append(current_get)
            results["voltage_get"].append(voltage_get)
            results["power"].append(power)

            self.stream_result.emit(
                {
                    "x": [linear(current_get, *config.CALIBRATION_CURR_2_FREQ)],
                    "y": [power],
                    "new_plot": step == 1,
                }
            )

            proc = round(step / config.KEITHLEY_CURRENT_POINTS * 100, 2)
            logger.info(f"[{proc} %][Time {round(time.time() - start_time, 1)} s]")

        keithley.set_current(initial_current)
        nrx.close()
        self.results.emit(results)
        self.finished.emit()


class MeasureTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.measureGraphWindow = None
        self.createGroupMeas()
        self.layout.addWidget(self.groupMeas)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def createGroupMeas(self):
        self.groupMeas = QGroupBox("Measure params")
        self.groupMeas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.keithleyFreqFromLabel = QLabel("Frequency from, GHz")
        self.keithleyFreqFrom = QDoubleSpinBox(self)
        self.keithleyFreqFrom.setRange(0, 20)
        self.keithleyFreqFrom.setDecimals(3)
        self.keithleyFreqFrom.setValue(config.KEITHLEY_FREQ_FROM)
        self.keithleyFreqFrom.valueChanged.connect(self.freq2curr)

        self.keithleyFreqToLabel = QLabel("Frequency to, GHz")
        self.keithleyFreqTo = QDoubleSpinBox(self)
        self.keithleyFreqTo.setRange(0, 20)
        self.keithleyFreqTo.setDecimals(3)
        self.keithleyFreqTo.setValue(config.KEITHLEY_FREQ_TO)
        self.keithleyFreqTo.valueChanged.connect(self.freq2curr)

        self.keithleyCurrentFromLabel = QLabel("~ 0 [A]")
        self.keithleyCurrentToLabel = QLabel("~ 0 [A]")

        self.keithleyCurrentPointsLabel = QLabel("Points count")
        self.keithleyCurrentPoints = QDoubleSpinBox(self)
        self.keithleyCurrentPoints.setRange(0, 1001)
        self.keithleyCurrentPoints.setDecimals(0)
        self.keithleyCurrentPoints.setValue(config.KEITHLEY_CURRENT_POINTS)

        self.btnStartMeas = QPushButton("Start Measure")
        self.btnStartMeas.clicked.connect(self.start_meas)

        self.btnStopMeas = QPushButton("Stop Measure")
        self.btnStopMeas.clicked.connect(self.stop_meas)

        layout.addWidget(self.keithleyFreqFromLabel, 1, 0)
        layout.addWidget(self.keithleyFreqFrom, 1, 1)
        layout.addWidget(self.keithleyCurrentFromLabel, 1, 2)
        layout.addWidget(self.keithleyFreqToLabel, 2, 0)
        layout.addWidget(self.keithleyFreqTo, 2, 1)
        layout.addWidget(self.keithleyCurrentToLabel, 2, 2)
        layout.addWidget(self.keithleyCurrentPointsLabel, 3, 0)
        layout.addWidget(self.keithleyCurrentPoints, 3, 1)
        layout.addWidget(self.btnStartMeas, 4, 0, 1, 2)
        layout.addWidget(self.btnStopMeas, 4, 2)

        self.groupMeas.setLayout(layout)
        self.freq2curr()

    def start_meas(self):
        self.meas_thread = QThread()
        self.meas_worker = MeasureWorker()
        self.meas_worker.moveToThread(self.meas_thread)

        config.KEITHLEY_MEAS = True
        self.freq2curr()
        config.KEITHLEY_CURRENT_POINTS = self.keithleyCurrentPoints.value()

        self.meas_thread.started.connect(self.meas_worker.run)
        self.meas_worker.finished.connect(self.meas_thread.quit)
        self.meas_worker.finished.connect(self.meas_worker.deleteLater)
        self.meas_thread.finished.connect(self.meas_thread.deleteLater)
        self.meas_worker.stream_result.connect(self.show_measure_graph_window)
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

    def freq2curr(self):
        config.KEITHLEY_CURRENT_FROM = linear(
            self.keithleyFreqFrom.value() * 1e9, *config.CALIBRATION_FREQ_2_CURR
        )
        config.KEITHLEY_CURRENT_TO = linear(
            self.keithleyFreqTo.value() * 1e9, *config.CALIBRATION_FREQ_2_CURR
        )
        self.keithleyCurrentFromLabel.setText(
            f"~ {round(config.KEITHLEY_CURRENT_FROM, 4)} [A]"
        )
        self.keithleyCurrentToLabel.setText(
            f"~ {round(config.KEITHLEY_CURRENT_TO, 4)} [A]"
        )

    def show_measure_graph_window(self, results: dict):
        if self.measureGraphWindow is None:
            self.measureGraphWindow = MeasureGraphWindow()
        self.measureGraphWindow.plotNew(
            x=results.get("x", []),
            y=results.get("y", []),
            new_plot=results.get("new_plot", True),
        )
        self.measureGraphWindow.show()
