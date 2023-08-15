import json
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
from api.ni import NiYIGManager
from api.rs_nrx import NRXBlock
from interface.components.Button import Button
from interface.components.DoubleSpinBox import DoubleSpinBox
from interface.components.GroupBox import GroupBox
from state import state
from interface.windows.stabilityMeasureGraphWindow import StabilityMeasureGraphWindow
from utils.functions import linear

logger = logging.getLogger(__name__)


class MeasureWorker(QObject):
    finished = pyqtSignal()
    results = pyqtSignal(list)
    stream_result = pyqtSignal(dict)

    def run(self):
        ni = NiYIGManager()
        nrx = NRXBlock(
            ip=state.NRX_IP,
            filter_time=state.NRX_FILTER_TIME,
            aperture_time=state.NRX_APER_TIME,
        )

        results = []
        freq_range = np.linspace(
            state.NI_FREQ_FROM,
            state.NI_FREQ_TO,
            int(state.NI_FREQ_POINTS),
        )
        start_time = time.time()
        for step, freq in enumerate(freq_range, 1):
            result = {
                "frequency": freq * 1e9,
                "power": [],
                "time": [],
            }
            if not state.NI_STABILITY_MEAS:
                break
            freq_point = linear(freq * 1e9, *state.CALIBRATION_DIGITAL_FREQ_2_POINT)
            ni.write_task(freq_point)
            time.sleep(0.01)
            if step == 1:
                time.sleep(0.4)
            tm = time.time()
            for i in range(state.NRX_POINTS):
                power = nrx.get_power()
                result["power"].append(power)
                result["time"].append(time.time() - tm)

                self.stream_result.emit(
                    {
                        "x": [time.time() - tm],
                        "y": [power],
                        "new_plot": i == 0,
                    }
                )

            results.append(result)

            proc = round(step / state.NI_FREQ_POINTS * 100, 2)
            logger.info(
                f"[{proc} %][Time {round(time.time() - start_time, 1)} s][Freq {freq}]"
            )

        nrx.close()
        self.results.emit(results)
        self.finished.emit()


class MeasureTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.stabilityMeasureGraphWindow = None
        self.createGroupMeas()
        self.layout.addWidget(self.groupMeas)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def createGroupMeas(self):
        self.groupMeas = GroupBox("Stability Digital Power(frequency)")
        self.groupMeas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.niFreqStartLabel = QLabel(self)
        self.niFreqStartLabel.setText("Frequency start, GHz")
        self.niFreqStart = DoubleSpinBox(self)
        self.niFreqStart.setRange(0, 20)
        self.niFreqStart.setDecimals(3)
        self.niFreqStart.setValue(state.NI_FREQ_FROM)

        self.niFreqStopLabel = QLabel(self)
        self.niFreqStopLabel.setText("Frequency stop, GHz")
        self.niFreqStop = DoubleSpinBox(self)
        self.niFreqStop.setRange(0, 20)
        self.niFreqStop.setDecimals(3)
        self.niFreqStop.setValue(state.NI_FREQ_TO)

        self.niFreqPointsLabel = QLabel(self)
        self.niFreqPointsLabel.setText("Freq points")
        self.niFreqPoints = DoubleSpinBox(self)
        self.niFreqPoints.setRange(0, 1001)
        self.niFreqPoints.setDecimals(0)
        self.niFreqPoints.setValue(state.NI_FREQ_POINTS)

        self.nrxPointsLabel = QLabel(self)
        self.nrxPointsLabel.setText("Power points")
        self.nrxPoints = DoubleSpinBox(self)
        self.nrxPoints.setRange(0, 1001)
        self.nrxPoints.setDecimals(0)
        self.nrxPoints.setValue(state.NRX_POINTS)

        self.btnStartMeas = Button("Start Measure")
        self.btnStartMeas.clicked.connect(self.start_meas)

        self.btnStopMeas = Button("Stop Measure")
        self.btnStopMeas.clicked.connect(self.stop_meas)

        layout.addWidget(self.niFreqStartLabel, 1, 0)
        layout.addWidget(self.niFreqStart, 1, 1)
        layout.addWidget(self.niFreqStopLabel, 2, 0)
        layout.addWidget(self.niFreqStop, 2, 1)
        layout.addWidget(self.niFreqPointsLabel, 3, 0)
        layout.addWidget(self.niFreqPoints, 3, 1)
        layout.addWidget(self.nrxPointsLabel, 4, 0)
        layout.addWidget(self.nrxPoints, 4, 1)
        layout.addWidget(self.btnStartMeas, 5, 0)
        layout.addWidget(self.btnStopMeas, 5, 1)

        self.groupMeas.setLayout(layout)

    def start_meas(self):
        self.meas_thread = QThread()
        self.meas_worker = MeasureWorker()
        self.meas_worker.moveToThread(self.meas_thread)

        state.NI_STABILITY_MEAS = True
        state.NI_FREQ_TO = self.niFreqStop.value()
        state.NI_FREQ_FROM = self.niFreqStart.value()
        state.NI_FREQ_POINTS = int(self.niFreqPoints.value())
        state.NRX_POINTS = int(self.nrxPoints.value())

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
        state.NI_STABILITY_MEAS = False

    def save_meas(self, results: list):
        try:
            filepath = QFileDialog.getSaveFileName(filter="*.json")[0]
            if not filepath.endswith(".json"):
                filepath += ".json"
            with open(filepath, "w", encoding="utf-8") as file:
                json.dump(results, file, ensure_ascii=False, indent=4)
        except (IndexError, FileNotFoundError):
            pass

    def show_measure_graph_window(self, results: dict):
        if self.stabilityMeasureGraphWindow is None:
            self.stabilityMeasureGraphWindow = StabilityMeasureGraphWindow()
        self.stabilityMeasureGraphWindow.plotNew(
            x=results.get("x", []),
            y=results.get("y", []),
            new_plot=results.get("new_plot", True),
        )
        self.stabilityMeasureGraphWindow.show()
