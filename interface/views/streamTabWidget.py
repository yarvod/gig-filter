import logging
import time
from typing import Dict

from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QCheckBox,
)

from api.keithley_power_supply import KeithleyBlock
from api.ni import NiYIGManager
from api.rs_fsek30 import SpectrumBlock
from api.rs_nrx import NRXBlock
from interface.components.Button import Button
from interface.components.DoubleSpinBox import DoubleSpinBox
from interface.components.GroupBox import GroupBox
from interface.windows.nrxStreamGraphWindow import NRXStreamGraphWindow
from interface.windows.spectrumGraphWindow import SpectrumGraphWindow
from state import state
from utils.functions import linear

logger = logging.getLogger(__name__)


class KeithleyStreamThread(QThread):
    current_get = pyqtSignal(float)
    voltage_get = pyqtSignal(float)

    def run(self):
        keithley = KeithleyBlock(
            address=state.KEITHLEY_ADDRESS, prologix_ip=state.PROLOGIX_IP
        )
        while state.KEITHLEY_STREAM_THREAD:
            time.sleep(0.2)
            current_get = keithley.get_current()
            self.current_get.emit(current_get)
            voltage_get = keithley.get_voltage()
            self.voltage_get.emit(voltage_get)
        self.finished.emit()

    def terminate(self) -> None:
        state.KEITHLEY_STREAM_THREAD = False
        super().terminate()
        logger.info(f"[{self.__class__.__name__}.terminate] Terminated")

    def exit(self, returnCode: int = ...) -> None:
        state.KEITHLEY_STREAM_THREAD = False
        super().exit(returnCode)
        logger.info(f"[{self.__class__.__name__}.exit] Exited")

    def quit(self) -> None:
        state.KEITHLEY_STREAM_THREAD = False
        super().quit()
        logger.info(f"[{self.__class__.__name__}.quit] Quited")


class KeithleySetCurrentThread(QThread):
    def run(self):
        keithley = KeithleyBlock(
            address=state.KEITHLEY_ADDRESS, prologix_ip=state.PROLOGIX_IP
        )
        keithley.set_current(state.KEITHLEY_CURRENT_SET)
        self.finished.emit()


class KeithleySetVoltageThread(QThread):
    def run(self):
        keithley = KeithleyBlock(address=state.KEITHLEY_ADDRESS)
        keithley.set_voltage(state.KEITHLEY_VOLTAGE_SET)
        self.finished.emit()


class NRXBlockStreamThread(QThread):
    meas = pyqtSignal(dict)

    def run(self):
        nrx = NRXBlock(
            ip=state.NRX_IP,
            filter_time=state.NRX_FILTER_TIME,
            aperture_time=state.NRX_APER_TIME,
        )
        i = 0
        start_time = time.time()
        while state.NRX_STREAM_THREAD:
            power = nrx.get_power()
            meas_time = time.time() - start_time
            if not power:
                time.sleep(2)
                continue

            self.meas.emit({"power": power, "time": meas_time, "reset": i == 0})
            i += 1
        self.finished.emit()

    def terminate(self) -> None:
        state.NRX_STREAM_THREAD = False
        super().terminate()
        logger.info(f"[{self.__class__.__name__}.terminate] Terminated")

    def exit(self, returnCode: int = ...) -> None:
        state.NRX_STREAM_THREAD = False
        super().exit(returnCode)
        logger.info(f"[{self.__class__.__name__}.exit] Exited")

    def quit(self) -> None:
        state.NRX_STREAM_THREAD = False
        super().quit()
        logger.info(f"[{self.__class__.__name__}.quit] Quited")


class DigitalYigThread(QThread):
    def run(self):
        value = int(
            linear(
                state.DIGITAL_YIG_FREQ * 1e9, *state.CALIBRATION_DIGITAL_FREQ_2_POINT
            )
        )
        ni_yig = NiYIGManager(host=state.NI_IP)
        resp = ni_yig.write_task(value=value)
        logger.info(f"[setNiYigFreq] {resp.json()}")


class SpectrumThread(QThread):
    data = pyqtSignal(dict)

    def run(self):
        block = SpectrumBlock()
        while 1:
            power = block.get_trace_data()
            self.data.emit(
                {
                    "x": list(range(len(power))),
                    "y": power,
                }
            )
            time.sleep(0.5)


class StreamTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.powerStreamGraphWindow = None
        self.spectrumStreamGraphWindow = None
        self.createGroupNRX()
        self.createGroupKeithley()
        self.createGroupNiYig()
        self.createGroupSpectrum()
        self.layout.addWidget(self.groupNRX)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.groupKeithley)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.groupNiYig)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.groupSpectrum)
        self.layout.addStretch()
        self.setLayout(self.layout)
        self.curr2freq()

    def createGroupNRX(self):
        self.groupNRX = GroupBox("Power meter monitor")
        self.groupNRX.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.nrxPowerLabel = QLabel(self)
        self.nrxPowerLabel.setText("<h4>Power, dBm</h4>")
        self.nrxPowerLabel.setStyleSheet("color: black;")
        self.nrxPower = QLabel(self)
        self.nrxPower.setText("0.0")
        self.nrxPower.setStyleSheet("font-size: 23px; font-weight: bold; color: black;")

        self.btnStartStreamNRX = Button("Start Stream")
        self.btnStartStreamNRX.clicked.connect(self.start_stream_nrx)

        self.btnStopStreamNRX = Button("Stop Stream")
        self.btnStopStreamNRX.setEnabled(False)
        self.btnStopStreamNRX.clicked.connect(self.stop_stream_nrx)

        self.checkNRXStreamPlot = QCheckBox(self)
        self.checkNRXStreamPlot.setText("Plot stream time line")

        self.nrxStreamPlotPointsLabel = QLabel(self)
        self.nrxStreamPlotPointsLabel.setText("Window points")
        self.nrxStreamPlotPoints = DoubleSpinBox(self)
        self.nrxStreamPlotPoints.setRange(10, 1000)
        self.nrxStreamPlotPoints.setDecimals(0)
        self.nrxStreamPlotPoints.setValue(state.NRX_STREAM_GRAPH_POINTS)

        layout.addWidget(
            self.nrxPowerLabel, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.nrxPower, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(
            self.btnStartStreamNRX, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.btnStopStreamNRX, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.checkNRXStreamPlot, 3, 0, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.nrxStreamPlotPointsLabel, 4, 0, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.nrxStreamPlotPoints, 4, 1, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.groupNRX.setLayout(layout)

    def createGroupKeithley(self):
        self.groupKeithley = GroupBox("Analog YIG (Power Supply)")
        self.groupKeithley.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.keithleyVoltageGetLabel = QLabel(self)
        self.keithleyVoltageGetLabel.setText("<h4>Voltage, V</h4>")
        self.keithleyVoltageGetLabel.setStyleSheet("color: black;")
        self.keithleyVoltageGet = QLabel(self)
        self.keithleyVoltageGet.setText("0.0")
        self.keithleyVoltageGet.setStyleSheet(
            "font-size: 23px; font-weight: bold; color: black;"
        )

        self.keithleyCurrentGetLabel = QLabel(self)
        self.keithleyCurrentGetLabel.setText("<h4>Current, A</h4>")
        self.keithleyCurrentGetLabel.setStyleSheet("color: black;")
        self.keithleyCurrentGet = QLabel(self)
        self.keithleyCurrentGet.setText("0.0")
        self.keithleyCurrentGet.setStyleSheet(
            "font-size: 23px; font-weight: bold; color: black;"
        )

        self.keithleyFreqGetLabel = QLabel(self)
        self.keithleyFreqGetLabel.setText("<h4>YIG frequency, GHz</h4>")
        self.keithleyFreqGetLabel.setStyleSheet("color: black;")

        self.keithleyFreqGet = QLabel(self)
        self.keithleyFreqGet.setText("0.0")
        self.keithleyFreqGet.setStyleSheet(
            "font-size: 23px; font-weight: bold; color: black;"
        )

        self.btnStartStreamKeithley = Button("Start Stream")
        self.btnStartStreamKeithley.clicked.connect(self.start_stream_keithley)

        self.btnStopStreamKeithley = Button("Stop Stream")
        self.btnStopStreamKeithley.setEnabled(False)
        self.btnStopStreamKeithley.clicked.connect(self.stop_stream_keithley)

        self.keithleyVoltageSetLabel = QLabel(self)
        self.keithleyVoltageSetLabel.setText("Voltage set, V")
        self.keithleyVoltageSet = DoubleSpinBox(self)
        self.keithleyVoltageSet.setRange(0, 30)
        self.keithleyVoltageSet.setDecimals(3)

        self.btnKeithleyVoltageSet = Button("Set voltage")
        self.btnKeithleyVoltageSet.clicked.connect(self.keithley_set_voltage)

        self.keithleyCurrentSetLabel = QLabel(self)
        self.keithleyCurrentSetLabel.setText("Current set, A")
        self.keithleyCurrentSet = DoubleSpinBox(self)
        self.keithleyCurrentSet.setRange(0.0827, 5)
        self.keithleyCurrentSet.setDecimals(4)
        self.keithleyCurrentSet.valueChanged.connect(self.curr2freq)

        self.btnKeithleyCurrentSet = Button("Set current")
        self.btnKeithleyCurrentSet.clicked.connect(self.keithley_set_current)

        self.keithleyFreqLabel = QLabel(self)
        self.keithleyFreqLabel.setText("Frequency set, GHz")
        self.keithleyFreq = DoubleSpinBox(self)
        self.keithleyFreq.setRange(3, 13)
        self.keithleyFreq.setValue(8)
        self.keithleyFreq.valueChanged.connect(self.freq2curr)

        self.btnKeithleyFreqSet = Button("Set frequency")
        self.btnKeithleyFreqSet.clicked.connect(self.keithley_set_current)

        layout.addWidget(
            self.keithleyVoltageGetLabel, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.keithleyCurrentGetLabel, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.keithleyFreqGetLabel, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.keithleyVoltageGet, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.keithleyCurrentGet, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(
            self.keithleyFreqGet, 2, 2, alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.btnStartStreamKeithley, 3, 0)
        layout.addWidget(self.btnStopStreamKeithley, 3, 2)
        layout.addWidget(self.keithleyVoltageSetLabel, 4, 0)
        layout.addWidget(self.keithleyVoltageSet, 4, 1)
        layout.addWidget(self.btnKeithleyVoltageSet, 4, 2)
        layout.addWidget(self.keithleyCurrentSetLabel, 5, 0)
        layout.addWidget(self.keithleyCurrentSet, 5, 1)
        layout.addWidget(self.btnKeithleyCurrentSet, 5, 2)
        layout.addWidget(self.keithleyFreqLabel, 6, 0)
        layout.addWidget(self.keithleyFreq, 6, 1)
        layout.addWidget(self.btnKeithleyFreqSet, 6, 2)

        self.groupKeithley.setLayout(layout)

    def createGroupNiYig(self):
        self.groupNiYig = GroupBox("Digital YIG (NI)")
        self.groupNiYig.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.niYigFreqLabel = QLabel(self)
        self.niYigFreqLabel.setText("Freq, GHz")
        self.niYigFreq = DoubleSpinBox(self)
        self.niYigFreq.setRange(2.94, 13)
        self.niYigFreq.setValue(state.DIGITAL_YIG_FREQ)

        self.btnSetNiYigFreq = Button("Set frequency")
        self.btnSetNiYigFreq.clicked.connect(self.setNiYigFreq)

        layout.addWidget(self.niYigFreqLabel, 1, 0)
        layout.addWidget(self.niYigFreq, 1, 1)
        layout.addWidget(self.btnSetNiYigFreq, 2, 0, 1, 2)

        self.groupNiYig.setLayout(layout)

    def createGroupSpectrum(self):
        self.groupSpectrum = GroupBox(self)
        self.groupSpectrum.setTitle("Spectrum")
        layout = QVBoxLayout()

        self.btnStartSpectrum = Button("Start stream spectrum")
        self.btnStartSpectrum.clicked.connect(self.startStreamSpectrum)
        self.btnStopSpectrum = Button("Stop stream spectrum")
        self.btnStopSpectrum.clicked.connect(lambda: self.spectrum_thread.terminate())
        self.btnStopSpectrum.setEnabled(False)

        layout.addWidget(self.btnStartSpectrum)
        layout.addWidget(self.btnStopSpectrum)
        self.groupSpectrum.setLayout(layout)

    def startStreamSpectrum(self):
        self.spectrum_thread = SpectrumThread()
        self.spectrum_thread.data.connect(self.show_spectrum)
        self.spectrum_thread.start()
        self.btnStartSpectrum.setEnabled(False)
        self.btnStopSpectrum.setEnabled(True)
        self.spectrum_thread.finished.connect(
            lambda: self.btnStartSpectrum.setEnabled(True)
        )
        self.spectrum_thread.finished.connect(
            lambda: self.btnStopSpectrum.setEnabled(False)
        )

    def show_spectrum(self, data: Dict):
        if self.spectrumStreamGraphWindow is None:
            self.spectrumStreamGraphWindow = SpectrumGraphWindow()

        self.spectrumStreamGraphWindow.plotNew(x=data["x"], y=data["y"])
        self.spectrumStreamGraphWindow.show()

    def setNiYigFreq(self):
        state.DIGITAL_YIG_FREQ = self.niYigFreq.value()
        self.set_digital_yig_freq_thread = DigitalYigThread()
        self.set_digital_yig_freq_thread.finished.connect(
            lambda: self.btnSetNiYigFreq.setEnabled(True)
        )
        self.set_digital_yig_freq_thread.start()
        self.btnSetNiYigFreq.setEnabled(False)

    def keithley_set_current(self):
        self.keithley_set_current_thread = KeithleySetCurrentThread()

        state.KEITHLEY_CURRENT_SET = self.keithleyCurrentSet.value()

        self.keithley_set_current_thread.start()

        self.btnKeithleyCurrentSet.setEnabled(False)
        self.keithley_set_current_thread.finished.connect(
            lambda: self.btnKeithleyCurrentSet.setEnabled(True)
        )

    def curr2freq(self):
        freq = linear(self.keithleyCurrentSet.value(), *state.CALIBRATION_CURR_2_FREQ)
        value = round(freq / 1e9, 2)
        self.keithleyFreq.setValue(value)

    def freq2curr(self):
        curr = linear(self.keithleyFreq.value() * 1e9, *state.CALIBRATION_FREQ_2_CURR)
        value = round(curr, 4)
        self.keithleyCurrentSet.setValue(value)

    def keithley_set_voltage(self):
        self.keithley_set_voltage_thread = KeithleySetVoltageThread()

        state.KEITHLEY_VOLTAGE_SET = self.keithleyVoltageSet.value()

        self.keithley_set_voltage_thread.start()

        self.btnKeithleyVoltageSet.setEnabled(False)
        self.keithley_set_voltage_thread.finished.connect(
            lambda: self.btnKeithleyVoltageSet.setEnabled(True)
        )

    def start_stream_keithley(self):
        self.keithley_stream_thread = KeithleyStreamThread()

        state.KEITHLEY_STREAM_THREAD = True

        self.keithley_stream_thread.current_get.connect(
            lambda x: self.keithleyCurrentGet.setText(f"{round(x, 4)}")
        )
        self.keithley_stream_thread.voltage_get.connect(
            lambda x: self.keithleyVoltageGet.setText(f"{round(x, 4)}")
        )
        self.keithley_stream_thread.start()

        self.btnStartStreamKeithley.setEnabled(False)
        self.keithley_stream_thread.finished.connect(
            lambda: self.btnStartStreamKeithley.setEnabled(True)
        )

        self.btnStopStreamKeithley.setEnabled(True)
        self.keithley_stream_thread.finished.connect(
            lambda: self.btnStopStreamKeithley.setEnabled(False)
        )

    def stop_stream_keithley(self):
        self.keithley_stream_thread.terminate()

    def start_stream_nrx(self):
        self.nrx_stream_thread = NRXBlockStreamThread()

        state.NRX_STREAM_THREAD = True
        state.NRX_STREAM_PLOT_GRAPH = self.checkNRXStreamPlot.isChecked()
        state.NRX_STREAM_GRAPH_POINTS = int(self.nrxStreamPlotPoints.value())

        self.nrx_stream_thread.meas.connect(self.update_nrx_stream_values)
        self.nrx_stream_thread.start()

        self.btnStartStreamNRX.setEnabled(False)
        self.nrx_stream_thread.finished.connect(
            lambda: self.btnStartStreamNRX.setEnabled(True)
        )

        self.btnStopStreamNRX.setEnabled(True)
        self.nrx_stream_thread.finished.connect(
            lambda: self.btnStopStreamNRX.setEnabled(False)
        )

    def show_power_stream_graph(self, x: float, y: float, reset: bool = True):
        if self.powerStreamGraphWindow is None:
            self.powerStreamGraphWindow = NRXStreamGraphWindow()
        self.powerStreamGraphWindow.plotNew(x=x, y=y, reset_data=reset)
        self.powerStreamGraphWindow.show()

    def update_nrx_stream_values(self, measure: dict):
        self.nrxPower.setText(f"{round(measure.get('power'), 3)}")
        if state.NRX_STREAM_PLOT_GRAPH:
            self.show_power_stream_graph(
                x=measure.get("time"),
                y=measure.get("power"),
                reset=measure.get("reset"),
            )

    def stop_stream_nrx(self):
        self.nrx_stream_thread.quit()
        self.nrx_stream_thread.exit(0)
