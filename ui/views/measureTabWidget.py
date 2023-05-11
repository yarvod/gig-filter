import logging
import time

from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton, QDoubleSpinBox,
)

from api.keithley_power_supply import KeithleyBlock
from api.rs_nrx import NRXBlock
from config import config

logger = logging.getLogger(__name__)


class KeithleyStreamWorker(QObject):
    finished = pyqtSignal()
    current_get = pyqtSignal(float)
    voltage_get = pyqtSignal(float)
    keithley = None

    def run(self):
        self.keithley = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        while config.KEITHLEY_STREAM:
            time.sleep(0.2)
            current_get = self.keithley.get_current()
            self.current_get.emit(current_get)
            voltage_get = self.keithley.get_voltage()
            self.voltage_get.emit(voltage_get)

        self.keithley.close()
        self.finished.emit()


class KeithleySetCurrentWorker(QObject):
    finished = pyqtSignal()
    keithley = None

    def run(self):
        self.keithley = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        self.keithley.set_current(config.KEITHLEY_CURRENT_SET)
        self.keithley.close()
        self.finished.emit()


class KeithleySetVoltageWorker(QObject):
    finished = pyqtSignal()
    keithley = None

    def run(self):
        self.keithley = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        self.keithley.set_voltage(config.KEITHLEY_VOLTAGE_SET)
        self.keithley.close()
        self.finished.emit()


class NRXBlockStreamWorker(QObject):
    finished = pyqtSignal()
    power = pyqtSignal(float)

    def run(self):
        block = NRXBlock(ip=config.NRX_IP, avg_time=config.NRX_AVG_TIME)
        while config.NRX_STREAM:
            power = block.meas()
            self.power.emit(power)
        block.close()
        self.finished.emit()


class MeasureTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.createGroupNRX()
        self.createGroupKeithley()
        self.layout.addWidget(self.groupNRX)
        self.layout.addWidget(self.groupKeithley)
        self.setLayout(self.layout)

    def createGroupNRX(self):
        self.groupNRX = QGroupBox("NRX monitor")
        layout = QGridLayout()

        self.nrxPowerLabel = QLabel("<h4>Power, dBm</h4>")
        self.nrxPower = QLabel(self)
        self.nrxPower.setText("0.0")
        self.nrxPower.setStyleSheet("font-size: 23px; font-weight: bold;")

        self.btnStartStreamNRX = QPushButton("Start Stream")
        self.btnStartStreamNRX.clicked.connect(self.start_stream_nrx)

        self.btnStopStreamNRX = QPushButton("Stop Stream")
        self.btnStopStreamNRX.setEnabled(False)
        self.btnStopStreamNRX.clicked.connect(self.stop_stream_nrx)

        layout.addWidget(self.nrxPowerLabel, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.nrxPower, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btnStartStreamNRX, 3, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btnStopStreamNRX, 3, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        self.groupNRX.setLayout(layout)

    def createGroupKeithley(self):
        self.groupKeithley = QGroupBox("Keithley monitor")
        layout = QGridLayout()

        self.keithleyVoltageGetLabel = QLabel(self)
        self.keithleyVoltageGetLabel.setText("<h4>Voltage, V</h4>")
        self.keithleyVoltageGet = QLabel(self)
        self.keithleyVoltageGet.setText("0.0")
        self.keithleyVoltageGet.setStyleSheet("font-size: 23px; font-weight: bold;")

        self.keithleyCurrentGetLabel = QLabel(self)
        self.keithleyCurrentGetLabel.setText("<h4>Current, A</h4>")
        self.keithleyCurrentGet = QLabel(self)
        self.keithleyCurrentGet.setText("0.0")
        self.keithleyCurrentGet.setStyleSheet("font-size: 23px; font-weight: bold;")

        self.btnStartStreamKeithley = QPushButton("Start Stream")
        self.btnStartStreamKeithley.clicked.connect(self.start_stream_keithley)

        self.btnStopStreamKeithley = QPushButton("Stop Stream")
        self.btnStopStreamKeithley.setEnabled(False)
        self.btnStopStreamKeithley.clicked.connect(self.stop_stream_keithley)

        self.keithleyCurrentSetLabel = QLabel("Current set, A")
        self.keithleyCurrentSet = QDoubleSpinBox(self)
        self.keithleyCurrentSet.setRange(0, 5)
        self.keithleyCurrentSet.setDecimals(4)

        self.keithleyVoltageSetLabel = QLabel("Voltage set, V")
        self.keithleyVoltageSet = QDoubleSpinBox(self)
        self.keithleyVoltageSet.setRange(0, 30)
        self.keithleyVoltageSet.setDecimals(3)

        self.btnKeithleyCurrentSet = QPushButton("Set current")
        self.btnKeithleyCurrentSet.clicked.connect(self.keithley_set_current)

        self.btnKeithleyVoltageSet = QPushButton("Set voltage")
        self.btnKeithleyVoltageSet.clicked.connect(self.keithley_set_voltage)

        layout.addWidget(self.keithleyVoltageGetLabel, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.keithleyCurrentGetLabel, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.keithleyVoltageGet, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.keithleyCurrentGet, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btnStartStreamKeithley, 3, 0)
        layout.addWidget(self.btnStopStreamKeithley, 3, 1)
        layout.addWidget(self.keithleyVoltageSetLabel, 4, 0)
        layout.addWidget(self.keithleyVoltageSet, 4, 1)
        layout.addWidget(self.btnKeithleyVoltageSet, 4, 2)
        layout.addWidget(self.keithleyCurrentSetLabel, 5, 0)
        layout.addWidget(self.keithleyCurrentSet, 5, 1)
        layout.addWidget(self.btnKeithleyCurrentSet, 5, 2)

        self.groupKeithley.setLayout(layout)

    def keithley_set_current(self):
        self.keithley_set_current_thread = QThread()
        self.keithley_set_current_worker = KeithleySetCurrentWorker()
        self.keithley_set_current_worker.moveToThread(self.keithley_set_current_thread)

        config.KEITHLEY_CURRENT_SET = self.keithleyCurrentSet.value()

        self.keithley_set_current_thread.started.connect(self.keithley_set_current_worker.run)
        self.keithley_set_current_worker.finished.connect(self.keithley_set_current_thread.quit)
        self.keithley_set_current_worker.finished.connect(self.keithley_set_current_worker.deleteLater)
        self.keithley_set_current_thread.finished.connect(self.keithley_set_current_thread.deleteLater)
        self.keithley_set_current_thread.start()

        self.btnKeithleyCurrentSet.setEnabled(False)
        self.keithley_set_current_thread.finished.connect(lambda: self.btnKeithleyCurrentSet.setEnabled(True))

    def keithley_set_voltage(self):
        self.keithley_set_voltage_thread = QThread()
        self.keithley_set_voltage_worker = KeithleySetVoltageWorker()
        self.keithley_set_voltage_worker.moveToThread(self.keithley_set_voltage_thread)

        config.KEITHLEY_VOLTAGE_SET = self.keithleyVoltageSet.value()

        self.keithley_set_voltage_thread.started.connect(self.keithley_set_voltage_worker.run)
        self.keithley_set_voltage_worker.finished.connect(self.keithley_set_voltage_thread.quit)
        self.keithley_set_voltage_worker.finished.connect(self.keithley_set_voltage_worker.deleteLater)
        self.keithley_set_voltage_thread.finished.connect(self.keithley_set_voltage_thread.deleteLater)
        self.keithley_set_voltage_thread.start()

        self.btnKeithleyVoltageSet.setEnabled(False)
        self.keithley_set_voltage_thread.finished.connect(lambda: self.btnKeithleyVoltageSet.setEnabled(True))

    def start_stream_keithley(self):
        self.keithley_stream_thread = QThread()
        self.keithley_stream_worker = KeithleyStreamWorker()
        self.keithley_stream_worker.moveToThread(self.keithley_stream_thread)

        config.KEITHLEY_STREAM = True

        self.keithley_stream_thread.started.connect(self.keithley_stream_worker.run)
        self.keithley_stream_worker.finished.connect(self.keithley_stream_thread.quit)
        self.keithley_stream_worker.finished.connect(self.keithley_stream_worker.deleteLater)
        self.keithley_stream_thread.finished.connect(self.keithley_stream_thread.deleteLater)
        self.keithley_stream_worker.current_get.connect(lambda x: self.keithleyCurrentGet.setText(f"{round(x, 4)}"))
        self.keithley_stream_worker.voltage_get.connect(lambda x: self.keithleyVoltageGet.setText(f"{round(x, 4)}"))
        self.keithley_stream_thread.start()

        self.btnStartStreamKeithley.setEnabled(False)
        self.keithley_stream_thread.finished.connect(lambda: self.btnStartStreamKeithley.setEnabled(True))

        self.btnStopStreamKeithley.setEnabled(True)
        self.keithley_stream_thread.finished.connect(lambda: self.btnStopStreamKeithley.setEnabled(False))

    def stop_stream_keithley(self):
        config.KEITHLEY_STREAM = False

    def start_stream_nrx(self):
        self.nrx_stream_thread = QThread()
        self.nrx_stream_worker = NRXBlockStreamWorker()
        self.nrx_stream_worker.moveToThread(self.nrx_stream_thread)

        config.NRX_STREAM = True

        self.nrx_stream_thread.started.connect(self.nrx_stream_worker.run)
        self.nrx_stream_worker.finished.connect(self.nrx_stream_thread.quit)
        self.nrx_stream_worker.finished.connect(self.nrx_stream_worker.deleteLater)
        self.nrx_stream_thread.finished.connect(self.nrx_stream_thread.deleteLater)
        self.nrx_stream_worker.power.connect(lambda x: self.nrxPower.setText(f"{round(x, 3)}"))
        self.nrx_stream_thread.start()

        self.btnStartStreamNRX.setEnabled(False)
        self.nrx_stream_thread.finished.connect(lambda: self.btnStartStreamNRX.setEnabled(True))

        self.btnStopStreamNRX.setEnabled(True)
        self.nrx_stream_thread.finished.connect(lambda: self.btnStopStreamNRX.setEnabled(False))

    def stop_stream_nrx(self):
        config.NRX_STREAM = False


