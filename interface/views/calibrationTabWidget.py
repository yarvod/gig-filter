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
    QDoubleSpinBox,
    QFileDialog,
    QSizePolicy,
)

from api.keithley_power_supply import KeithleyBlock
from api.rs_fsek30 import SpectrumBlock
from interface.components.Button import Button
from interface.components.GroupBox import GroupBox
from state import state
from interface.windows.calibrationGraphWindow import CalibrationGraphWindow
from utils.functions import linear, linear_fit, truncate_path

logger = logging.getLogger(__name__)


class CalibrateWorker(QObject):
    finished = pyqtSignal()
    results = pyqtSignal(dict)
    stream_result = pyqtSignal(dict)

    def run(self):
        dc_block = KeithleyBlock(
            prologix_ip=state.PROLOGIX_IP, address=state.KEITHLEY_ADDRESS
        )
        s_block = SpectrumBlock(
            prologix_ip=state.PROLOGIX_IP, address=state.SPECTRUM_ADDRESS
        )

        results = {
            "current_set": [],
            "current_get": [],
            "voltage_get": [],
            "power": [],
            "freq": [],
        }
        current_range = list(
            np.linspace(
                state.KEITHLEY_CURRENT_FROM,
                state.KEITHLEY_CURRENT_TO,
                int(state.KEITHLEY_CURRENT_POINTS),
            )
        )
        current_range.extend(
            list(
                np.linspace(
                    state.KEITHLEY_CURRENT_TO,
                    state.KEITHLEY_CURRENT_FROM,
                    int(state.KEITHLEY_CURRENT_POINTS),
                )
            )
        )

        initial_current = dc_block.get_setted_current()

        for step, current in enumerate(current_range, 1):
            if not state.CALIBRATION_MEAS:
                break
            dc_block.set_current(current)
            time.sleep(state.CALIBRATION_STEP_DELAY)
            if step == 1:
                time.sleep(0.4)
            current_get = dc_block.get_current()
            voltage_get = dc_block.get_voltage()
            s_block.peak_search()
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

            proc = round(step / state.KEITHLEY_CURRENT_POINTS * 100, 2)
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
        self.createGroupCalibrationFiles()
        self.layout.addWidget(self.groupCalibration)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.groupCalibrationFiles)
        self.layout.addStretch()
        self.setLayout(self.layout)
        self.curr2freq()

    def createGroupCalibration(self):
        self.groupCalibration = GroupBox("Calibration params")
        self.groupCalibration.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.keithleyCurrentFromLabel = QLabel(self)
        self.keithleyCurrentFromLabel.setText("Current from, A")
        self.keithleyCurrentFrom = QDoubleSpinBox(self)
        self.keithleyCurrentFrom.setRange(0, 5)
        self.keithleyCurrentFrom.setValue(state.KEITHLEY_CURRENT_FROM)
        self.keithleyCurrentFrom.valueChanged.connect(self.curr2freq)

        self.keithleyFreqFrom = QLabel(self)
        self.keithleyFreqFrom.setText("~ 0 [GHz]")

        self.keithleyCurrentToLabel = QLabel(self)
        self.keithleyCurrentToLabel.setText("Current to, A")
        self.keithleyCurrentTo = QDoubleSpinBox(self)
        self.keithleyCurrentTo.setRange(0, 5)
        self.keithleyCurrentTo.setValue(state.KEITHLEY_CURRENT_TO)
        self.keithleyCurrentTo.valueChanged.connect(self.curr2freq)

        self.keithleyFreqTo = QLabel(self)
        self.keithleyFreqTo.setText("~ 0 [GHz]")

        self.keithleyCurrentPointsLabel = QLabel(self)
        self.keithleyCurrentPointsLabel.setText("Points count")
        self.keithleyCurrentPoints = QDoubleSpinBox(self)
        self.keithleyCurrentPoints.setRange(0, 1001)
        self.keithleyCurrentPoints.setDecimals(0)
        self.keithleyCurrentPoints.setValue(state.KEITHLEY_CURRENT_POINTS)

        self.calibrationStepDelayLabel = QLabel(self)
        self.calibrationStepDelayLabel.setText("Step delay, s")
        self.calibrationStepDelay = QDoubleSpinBox(self)
        self.calibrationStepDelay.setRange(0, 10)
        self.calibrationStepDelay.setValue(state.CALIBRATION_STEP_DELAY)

        self.btnStartMeas = Button("Start Calibration")
        self.btnStartMeas.clicked.connect(self.start_calibration)

        self.btnStopMeas = Button("Stop Calibration")
        self.btnStopMeas.clicked.connect(self.stop_calibration)

        layout.addWidget(self.keithleyCurrentFromLabel, 1, 0)
        layout.addWidget(self.keithleyCurrentFrom, 1, 1)
        layout.addWidget(self.keithleyFreqFrom, 1, 2)
        layout.addWidget(self.keithleyCurrentToLabel, 2, 0)
        layout.addWidget(self.keithleyCurrentTo, 2, 1)
        layout.addWidget(self.keithleyFreqTo, 2, 2)
        layout.addWidget(self.keithleyCurrentPointsLabel, 3, 0)
        layout.addWidget(self.keithleyCurrentPoints, 3, 1)
        layout.addWidget(self.calibrationStepDelayLabel, 4, 0)
        layout.addWidget(self.calibrationStepDelay, 4, 1)
        layout.addWidget(self.btnStartMeas, 5, 0, 1, 2)
        layout.addWidget(self.btnStopMeas, 5, 2)

        self.groupCalibration.setLayout(layout)

    def createGroupCalibrationFiles(self):
        self.groupCalibrationFiles = GroupBox("Calibration files")
        self.groupCalibrationFiles.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.calibrationFilePath = QLabel(self)
        self.calibrationFilePath.setText(f".../{truncate_path(state.CALIBRATION_FILE)}")
        self.calibrationFilePath.setToolTip(f"{state.CALIBRATION_FILE}")
        self.btnChooseCalibrationFile = Button("Choose file")
        self.btnChooseCalibrationFile.clicked.connect(self.chooseCalibrationFile)

        self.btnCalibrate = Button("Apply calibration")
        self.btnCalibrate.clicked.connect(self.apply_calibration)

        layout.addWidget(self.calibrationFilePath, 1, 0)
        layout.addWidget(self.btnChooseCalibrationFile, 1, 1)
        layout.addWidget(self.btnCalibrate, 2, 0, 2, 0)

        self.groupCalibrationFiles.setLayout(layout)

    def start_calibration(self):
        self.calibration_thread = QThread()
        self.calibration_worker = CalibrateWorker()
        self.calibration_worker.moveToThread(self.calibration_thread)

        state.CALIBRATION_MEAS = True
        state.KEITHLEY_CURRENT_FROM = self.keithleyCurrentFrom.value()
        state.KEITHLEY_CURRENT_TO = self.keithleyCurrentTo.value()
        state.KEITHLEY_CURRENT_POINTS = self.keithleyCurrentPoints.value()
        state.CALIBRATION_STEP_DELAY = self.calibrationStepDelay.value()

        self.calibration_thread.started.connect(self.calibration_worker.run)
        self.calibration_worker.finished.connect(self.calibration_thread.quit)
        self.calibration_worker.finished.connect(self.calibration_worker.deleteLater)
        self.calibration_thread.finished.connect(self.calibration_thread.deleteLater)
        self.calibration_worker.stream_result.connect(
            self.show_calibration_graph_window
        )
        self.calibration_worker.results.connect(self.save_calibration)
        self.calibration_thread.start()

        self.btnStartMeas.setEnabled(False)
        self.calibration_thread.finished.connect(
            lambda: self.btnStartMeas.setEnabled(True)
        )

        self.btnStopMeas.setEnabled(True)
        self.calibration_thread.finished.connect(
            lambda: self.btnStopMeas.setEnabled(False)
        )

    def stop_calibration(self):
        state.CALIBRATION_MEAS = False

    def save_calibration(self, results: dict):
        opt_1 = linear_fit(results["freq"], results["current_get"])
        opt_2 = linear_fit(results["current_get"], results["freq"])
        state.CALIBRATION_FREQ_2_CURR = list(opt_1)
        state.CALIBRATION_CURR_2_FREQ = list(opt_2)
        try:
            filepath = QFileDialog.getSaveFileName(
                caption="Save calibration file", filter=".csv"
            )[0]
            df = pd.DataFrame(
                {"frequency": results["freq"], "current": results["current_get"]}
            )
            df.to_csv(filepath)
        except (IndexError, FileNotFoundError):
            pass

    def chooseCalibrationFile(self):
        try:
            filepath = QFileDialog.getOpenFileName(
                caption="Choose calibration file", filter="*.csv"
            )[0]
            if filepath:
                self.calibrationFilePath.setText(f"{truncate_path(filepath)}")
                state.CALIBRATION_FILE = filepath
        except (IndexError, FileNotFoundError):
            return

    def apply_calibration(self):
        calibration = pd.read_csv(state.CALIBRATION_FILE)
        opt_1 = linear_fit(calibration["frequency"], calibration["current"])
        opt_2 = linear_fit(calibration["current"], calibration["frequency"])
        state.CALIBRATION_FREQ_2_CURR = list(opt_1)
        state.CALIBRATION_CURR_2_FREQ = list(opt_2)

    def show_calibration_graph_window(self, results: dict):
        if self.calibrationGraphWindow is None:
            self.calibrationGraphWindow = CalibrationGraphWindow()
        self.calibrationGraphWindow.plotNew(
            x=results.get("x", []),
            y=results.get("y", []),
            new_plot=results.get("new_plot", True),
        )
        self.calibrationGraphWindow.show()

    def curr2freq(self):
        freq_from = linear(
            self.keithleyCurrentFrom.value(), *state.CALIBRATION_CURR_2_FREQ
        )
        self.keithleyFreqFrom.setText(f"~ {round(freq_from / 1e9, 2)} [GHz]")
        freq_to = linear(self.keithleyCurrentTo.value(), *state.CALIBRATION_CURR_2_FREQ)
        self.keithleyFreqTo.setText(f"~ {round(freq_to / 1e9, 2)} [GHz]")
