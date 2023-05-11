import logging

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from api.keithley_power_supply import KeithleyBlock
from api.rs_nrx import NRXBlock
from config import config

logger = logging.getLogger(__name__)


class KeithleyWorker(QObject):
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        keithley = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        result = keithley.test()
        status = config.KEITHLEY_TEST_MAP.get(result, "Undefined Error")
        keithley.close()
        self.status.emit(status)
        self.finished.emit()


class KeithleyOutputWorker(QObject):
    finished = pyqtSignal()
    state = pyqtSignal(str)

    def run(self):
        keithley = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        result = keithley.set_output_state(state=config.KEITHLEY_OUTPUT_STATE)
        state = keithley.get_output_state()
        keithley.close()
        self.state.emit(state)
        self.finished.emit()


class NRXBlockWorker(QObject):
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        block = NRXBlock(ip=config.NRX_IP)
        result = block.test()
        block.close()
        self.status.emit(config.NRX_TEST_MAP.get(result, "Error"))
        self.finished.emit()


class SetUpTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.createGroupNRX()
        self.createGroupKeithley()
        self.layout.addWidget(self.groupNRX)
        self.layout.addWidget(self.groupKeithley)
        self.setLayout(self.layout)

    def createGroupNRX(self):
        self.groupNRX = QGroupBox("NRX config")
        layout = QGridLayout()

        self.nrxIPLabel = QLabel(self)
        self.nrxIPLabel.setText("NRX IP:")
        self.nrxIP = QLineEdit(self)
        self.nrxIP.setText(config.NRX_IP)

        self.nrxStatusLabel = QLabel(self)
        self.nrxStatusLabel.setText("NRX status:")
        self.nrxStatus = QLabel(self)
        self.nrxStatus.setText("NRX is not initialized yet!")

        self.btnInitNRX = QPushButton("Initialize NRX")
        self.btnInitNRX.clicked.connect(self.initialize_nrx)

        layout.addWidget(self.nrxIPLabel, 1, 0)
        layout.addWidget(self.nrxIP, 1, 1)
        layout.addWidget(self.nrxStatusLabel, 2, 0)
        layout.addWidget(self.nrxStatus, 2, 1)
        layout.addWidget(self.btnInitNRX, 3, 0, 1, 2)

        self.groupNRX.setLayout(layout)

    def createGroupKeithley(self):
        self.groupKeithley = QGroupBox("Keithley config")
        layout = QGridLayout()

        self.keithleyAddressLabel = QLabel(self)
        self.keithleyAddressLabel.setText("Keithley address:")
        self.keithleyAddress = QLineEdit(self)
        self.keithleyAddress.setText(config.KEITHLEY_ADDRESS)

        self.keithleyStatusLabel = QLabel(self)
        self.keithleyStatusLabel.setText("Keithley status:")
        self.keithleyStatus = QLabel(self)
        self.keithleyStatus.setText("Keithley is not checked yet!")

        self.btnInitKeithley = QPushButton("Initialize Keithley")
        self.btnInitKeithley.clicked.connect(self.initialize_keithley)

        self.keithleyStateLabel = QLabel("Output On/Off:")

        self.btnKeithleyState = QPushButton("Off")
        self.btnKeithleyState.clicked.connect(self.set_keithley_state)

        layout.addWidget(self.keithleyAddressLabel, 1, 0)
        layout.addWidget(self.keithleyAddress, 1, 1)
        layout.addWidget(self.keithleyStatusLabel, 2, 0)
        layout.addWidget(self.keithleyStatus, 2, 1)
        layout.addWidget(self.btnInitKeithley, 3, 0, 1, 2)
        layout.addWidget(self.keithleyStateLabel, 4, 0)
        layout.addWidget(self.btnKeithleyState, 4, 1,)

        self.groupKeithley.setLayout(layout)

    def set_keithley_btn_state(self, state: str):
        text = config.KEITHLEY_OUTPUT_STATE_MAP.get(state)
        self.btnKeithleyState.setText(f"{text}")

    def set_keithley_state(self):
        self.keithley_state_thread = QThread()
        self.keithley_state_worker = KeithleyOutputWorker()

        config.KEITHLEY_OUTPUT_STATE = config.KEITHLEY_OUTPUT_STATE_MAP_REVERSE.get(self.btnKeithleyState.text(), "0")

        self.keithley_state_worker.moveToThread(self.keithley_state_thread)
        self.keithley_state_thread.started.connect(self.keithley_state_worker.run)
        self.keithley_state_worker.finished.connect(self.keithley_state_thread.quit)
        self.keithley_state_worker.finished.connect(self.keithley_state_worker.deleteLater)
        self.keithley_state_thread.finished.connect(self.keithley_state_thread.deleteLater)
        self.keithley_state_worker.state.connect(self.set_keithley_btn_state)
        self.keithley_state_thread.start()

        self.btnKeithleyState.setEnabled(False)
        self.keithley_state_thread.finished.connect(lambda: self.btnKeithleyState.setEnabled(True))

    def set_nrx_status(self, status: str):
        self.nrxStatus.setText(status)

    def initialize_nrx(self):
        self.nrx_thread = QThread()
        self.nrx_worker = NRXBlockWorker()

        config.NRX_IP = self.nrxIP.text()

        self.nrx_worker.moveToThread(self.nrx_thread)
        self.nrx_thread.started.connect(self.nrx_worker.run)
        self.nrx_worker.finished.connect(self.nrx_thread.quit)
        self.nrx_worker.finished.connect(self.nrx_worker.deleteLater)
        self.nrx_thread.finished.connect(self.nrx_thread.deleteLater)
        self.nrx_worker.status.connect(self.set_nrx_status)
        self.nrx_thread.start()

        self.btnInitNRX.setEnabled(False)
        self.nrx_thread.finished.connect(lambda: self.btnInitNRX.setEnabled(True))

    def set_keithley_status(self, status: str):
        self.keithleyStatus.setText(status)

    def initialize_keithley(self):
        self.keithley_thread = QThread()
        self.keithley_worker = KeithleyWorker()

        config.KEITHLEY_ADDRESS = self.keithleyAddress.text()

        self.keithley_worker.moveToThread(self.keithley_thread)
        self.keithley_thread.started.connect(self.keithley_worker.run)
        self.keithley_worker.finished.connect(self.keithley_thread.quit)
        self.keithley_worker.finished.connect(self.keithley_worker.deleteLater)
        self.keithley_thread.finished.connect(self.keithley_thread.deleteLater)
        self.keithley_worker.status.connect(self.set_keithley_status)
        self.keithley_thread.start()

        self.btnInitKeithley.setEnabled(False)
        self.keithley_thread.finished.connect(lambda: self.btnInitKeithley.setEnabled(True))
