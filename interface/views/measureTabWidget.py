import logging
import time

import numpy as np
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFileDialog,
    QSizePolicy,
)

from api.keithley_power_supply import KeithleyBlock
from api.rs_nrx import NRXBlock
from interface.components.Button import Button
from interface.components.DoubleSpinBox import DoubleSpinBox
from interface.components.GroupBox import GroupBox
from state import state
from interface.windows.measureGraphWindow import MeasureGraphWindow
from utils.functions import linear

logger = logging.getLogger(__name__)


class MeasureWorker(QObject):
    finished = pyqtSignal()
    results = pyqtSignal(dict)
    stream_result = pyqtSignal(dict)

    def run(self):
        keithley = KeithleyBlock(address=state.KEITHLEY_ADDRESS)
        nrx = NRXBlock(
            ip=state.NRX_IP,
            filter_time=state.NRX_FILTER_TIME,
            aperture_time=state.NRX_APER_TIME,
        )

        results = {
            "current_set": [],
            "current_get": [],
            "voltage_get": [],
            "power": [],
        }
        current_range = np.linspace(
            state.KEITHLEY_CURRENT_FROM,
            state.KEITHLEY_CURRENT_TO,
            int(state.KEITHLEY_CURRENT_POINTS),
        )
        start_time = time.time()
        initial_current = keithley.get_setted_current()
        for step, current in enumerate(current_range, 1):
            if not state.KEITHLEY_MEAS:
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
                    "x": [linear(current_get, *state.CALIBRATION_CURR_2_FREQ)],
                    "y": [power],
                    "new_plot": step == 1,
                }
            )

            proc = round(step / state.KEITHLEY_CURRENT_POINTS * 100, 2)
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
        self.groupMeas = GroupBox("Measure params")
        self.groupMeas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.keithleyFreqFromLabel = QLabel(self)
        self.keithleyFreqFromLabel.setText("Frequency from, GHz")
        self.keithleyFreqFrom = DoubleSpinBox(self)
        self.keithleyFreqFrom.setRange(0, 20)
        self.keithleyFreqFrom.setDecimals(3)
        self.keithleyFreqFrom.setValue(state.KEITHLEY_FREQ_FROM)
        self.keithleyFreqFrom.valueChanged.connect(self.freq2curr)

        self.keithleyFreqToLabel = QLabel(self)
        self.keithleyFreqToLabel.setText("Frequency to, GHz")
        self.keithleyFreqTo = DoubleSpinBox(self)
        self.keithleyFreqTo.setRange(0, 20)
        self.keithleyFreqTo.setDecimals(3)
        self.keithleyFreqTo.setValue(state.KEITHLEY_FREQ_TO)
        self.keithleyFreqTo.valueChanged.connect(self.freq2curr)

        self.keithleyCurrentFromLabel = QLabel(self)
        self.keithleyCurrentFromLabel.setText("~ 0 [A]")
        self.keithleyCurrentToLabel = QLabel(self)
        self.keithleyCurrentToLabel.setText("~ 0 [A]")

        self.keithleyCurrentPointsLabel = QLabel(self)
        self.keithleyCurrentPointsLabel.setText("Points count")
        self.keithleyCurrentPoints = DoubleSpinBox(self)
        self.keithleyCurrentPoints.setRange(0, 1001)
        self.keithleyCurrentPoints.setDecimals(0)
        self.keithleyCurrentPoints.setValue(state.KEITHLEY_CURRENT_POINTS)

        self.btnStartMeas = Button("Start Measure")
        self.btnStartMeas.clicked.connect(self.start_meas)

        self.btnStopMeas = Button("Stop Measure")
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

        state.KEITHLEY_MEAS = True
        self.freq2curr()
        state.KEITHLEY_CURRENT_POINTS = self.keithleyCurrentPoints.value()

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
        state.KEITHLEY_MEAS = False

    def save_meas(self, results: dict):
        try:
            filepath = QFileDialog.getSaveFileName()[0]
            df = pd.DataFrame(results)
            df.to_csv(filepath)
        except (IndexError, FileNotFoundError):
            pass

    def freq2curr(self):
        state.KEITHLEY_CURRENT_FROM = linear(
            self.keithleyFreqFrom.value() * 1e9, *state.CALIBRATION_FREQ_2_CURR
        )
        state.KEITHLEY_CURRENT_TO = linear(
            self.keithleyFreqTo.value() * 1e9, *state.CALIBRATION_FREQ_2_CURR
        )
        self.keithleyCurrentFromLabel.setText(
            f"~ {round(state.KEITHLEY_CURRENT_FROM, 4)} [A]"
        )
        self.keithleyCurrentToLabel.setText(
            f"~ {round(state.KEITHLEY_CURRENT_TO, 4)} [A]"
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
