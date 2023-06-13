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
    QDoubleSpinBox,
    QSizePolicy,
)

from api.keithley_power_supply import KeithleyBlock
from api.rs_fsek30 import SpectrumBlock
from api.rs_nrx import NRXBlock
from config import config

logger = logging.getLogger(__name__)


class KeithleyWorker(QObject):
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        keithley = KeithleyBlock(
            address=config.KEITHLEY_ADDRESS, prologix_ip=config.PROLOGIX_IP
        )
        result = keithley.test()
        status = config.KEITHLEY_TEST_MAP.get(result, "Undefined Error")
        self.status.emit(status)
        self.finished.emit()


class RsSpectrumWorker(QObject):
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        spectrum = SpectrumBlock(
            address=config.SPECTRUM_ADDRESS,
        )
        result = spectrum.idn()
        status = "Ok" if "FSEK" in result else "Undefined Error"
        self.status.emit(status)
        self.finished.emit()


class KeithleyOutputWorker(QObject):
    finished = pyqtSignal()
    state = pyqtSignal(str)

    def run(self):
        keithley = KeithleyBlock(address=config.KEITHLEY_ADDRESS)
        keithley.set_output_state(state=config.KEITHLEY_OUTPUT_STATE)
        state = keithley.get_output_state()
        self.state.emit(state)
        self.finished.emit()


class NRXBlockWorker(QObject):
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        block = NRXBlock(
            ip=config.NRX_IP,
            aperture_time=config.NRX_APER_TIME,
        )
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
        self.createGroupRsSpectrumAnalyzer()
        self.layout.addWidget(self.groupNRX)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.groupKeithley)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.groupRsSpectrum)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def createGroupNRX(self):
        self.groupNRX = QGroupBox("Power meter config")
        self.groupNRX.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.nrxIPLabel = QLabel(self)
        self.nrxIPLabel.setText("PM IP:")
        self.nrxIP = QLineEdit(self)
        self.nrxIP.setText(config.NRX_IP)

        self.nrxAperTimeLabel = QLabel(self)
        self.nrxAperTimeLabel.setText("PM Averaging time, s:")
        self.nrxAperTime = QDoubleSpinBox(self)
        self.nrxAperTime.setDecimals(5)
        self.nrxAperTime.setRange(1e-5, 1000)
        self.nrxAperTime.setValue(config.NRX_APER_TIME)

        self.nrxStatusLabel = QLabel(self)
        self.nrxStatusLabel.setText("PM status:")
        self.nrxStatus = QLabel(self)
        self.nrxStatus.setText("PM is not initialized yet!")

        self.btnInitNRX = QPushButton("Initialize PM")
        self.btnInitNRX.clicked.connect(self.initialize_nrx)

        layout.addWidget(self.nrxIPLabel, 1, 0)
        layout.addWidget(self.nrxIP, 1, 1)
        layout.addWidget(self.nrxAperTimeLabel, 2, 0)
        layout.addWidget(self.nrxAperTime, 2, 1)
        layout.addWidget(self.nrxStatusLabel, 3, 0)
        layout.addWidget(self.nrxStatus, 3, 1)
        layout.addWidget(self.btnInitNRX, 4, 0, 1, 2)

        self.groupNRX.setLayout(layout)

    def createGroupKeithley(self):
        self.groupKeithley = QGroupBox("Power supply config")
        self.groupKeithley.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.keithleyAddressLabel = QLabel(self)
        self.keithleyAddressLabel.setText("Power supply address:")
        self.keithleyAddress = QDoubleSpinBox(self)
        self.keithleyAddress.setRange(0, 31)
        self.keithleyAddress.setDecimals(0)
        self.keithleyAddress.setValue(config.KEITHLEY_ADDRESS)

        self.keithleyStatusLabel = QLabel(self)
        self.keithleyStatusLabel.setText("Power supply status:")
        self.keithleyStatus = QLabel(self)
        self.keithleyStatus.setText("Power supply is not checked yet!")

        self.btnInitKeithley = QPushButton("Initialize Power supply")
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
        layout.addWidget(
            self.btnKeithleyState,
            4,
            1,
        )

        self.groupKeithley.setLayout(layout)

    def createGroupRsSpectrumAnalyzer(self):
        self.groupRsSpectrum = QGroupBox("Spectrum Analyzer RS FSEK config")
        self.groupRsSpectrum.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.rsSpectrumAddressLabel = QLabel(self)
        self.rsSpectrumAddressLabel.setText("RS Spectrum address:")
        self.rsSpectrumAddress = QDoubleSpinBox(self)
        self.rsSpectrumAddress.setRange(0, 31)
        self.rsSpectrumAddress.setDecimals(0)
        self.rsSpectrumAddress.setValue(config.SPECTRUM_ADDRESS)

        self.rsSpectrumStatusLabel = QLabel(self)
        self.rsSpectrumStatusLabel.setText("RS Spectrum status:")
        self.rsSpectrumStatus = QLabel(self)
        self.rsSpectrumStatus.setText("RS Spectrum is not initialized yet!")

        self.btnInitRsSpectrum = QPushButton("Initialize RS Spectrum")
        self.btnInitRsSpectrum.clicked.connect(self.initialize_rs_spectrum)

        layout.addWidget(self.rsSpectrumAddressLabel, 1, 0)
        layout.addWidget(self.rsSpectrumAddress, 1, 1)
        layout.addWidget(self.rsSpectrumStatusLabel, 2, 0)
        layout.addWidget(self.rsSpectrumStatus, 2, 1)
        layout.addWidget(self.btnInitRsSpectrum, 3, 0, 1, 2)

        self.groupRsSpectrum.setLayout(layout)

    def set_keithley_btn_state(self, state: str):
        text = config.KEITHLEY_OUTPUT_STATE_MAP.get(state)
        self.btnKeithleyState.setText(f"{text}")

    def set_keithley_state(self):
        self.keithley_state_thread = QThread()
        self.keithley_state_worker = KeithleyOutputWorker()

        config.KEITHLEY_OUTPUT_STATE = config.KEITHLEY_OUTPUT_STATE_MAP_REVERSE.get(
            self.btnKeithleyState.text(), "0"
        )

        self.keithley_state_worker.moveToThread(self.keithley_state_thread)
        self.keithley_state_thread.started.connect(self.keithley_state_worker.run)
        self.keithley_state_worker.finished.connect(self.keithley_state_thread.quit)
        self.keithley_state_worker.finished.connect(
            self.keithley_state_worker.deleteLater
        )
        self.keithley_state_thread.finished.connect(
            self.keithley_state_thread.deleteLater
        )
        self.keithley_state_worker.state.connect(self.set_keithley_btn_state)
        self.keithley_state_thread.start()

        self.btnKeithleyState.setEnabled(False)
        self.keithley_state_thread.finished.connect(
            lambda: self.btnKeithleyState.setEnabled(True)
        )

    def set_nrx_status(self, status: str):
        self.nrxStatus.setText(status)

    def initialize_nrx(self):
        self.nrx_thread = QThread()
        self.nrx_worker = NRXBlockWorker()

        config.NRX_IP = self.nrxIP.text()
        config.NRX_APER_TIME = self.nrxAperTime.value()

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

        config.KEITHLEY_ADDRESS = int(self.keithleyAddress.value())

        self.keithley_worker.moveToThread(self.keithley_thread)
        self.keithley_thread.started.connect(self.keithley_worker.run)
        self.keithley_worker.finished.connect(self.keithley_thread.quit)
        self.keithley_worker.finished.connect(self.keithley_worker.deleteLater)
        self.keithley_thread.finished.connect(self.keithley_thread.deleteLater)
        self.keithley_worker.status.connect(self.set_keithley_status)
        self.keithley_thread.start()

        self.btnInitKeithley.setEnabled(False)
        self.keithley_thread.finished.connect(
            lambda: self.btnInitKeithley.setEnabled(True)
        )

    def initialize_rs_spectrum(self):
        self.rs_spectrum_thread = QThread()
        self.rs_spectrum_worker = RsSpectrumWorker()

        config.SPECTRUM_ADDRESS = int(self.rsSpectrumAddress.value())

        self.rs_spectrum_worker.moveToThread(self.rs_spectrum_thread)
        self.rs_spectrum_thread.started.connect(self.rs_spectrum_worker.run)
        self.rs_spectrum_worker.finished.connect(self.rs_spectrum_thread.quit)
        self.rs_spectrum_worker.finished.connect(self.rs_spectrum_worker.deleteLater)
        self.rs_spectrum_thread.finished.connect(self.rs_spectrum_thread.deleteLater)
        self.rs_spectrum_worker.status.connect(self.set_rs_spectrum_status)
        self.rs_spectrum_thread.start()

        self.btnInitRsSpectrum.setEnabled(False)
        self.rs_spectrum_thread.finished.connect(
            lambda: self.btnInitRsSpectrum.setEnabled(True)
        )

    def set_rs_spectrum_status(self, status: str):
        self.rsSpectrumStatus.setText(status)
