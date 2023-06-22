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
from api.prologixEthernet import PrologixGPIBEthernet
from api.rs_fsek30 import SpectrumBlock
from api.rs_nrx import NRXBlock
from state import state

logger = logging.getLogger(__name__)


class KeithleyWorker(QObject):
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        keithley = KeithleyBlock(
            address=state.KEITHLEY_ADDRESS, prologix_ip=state.PROLOGIX_IP
        )
        result = keithley.test()
        status = state.KEITHLEY_TEST_MAP.get(result, "Undefined Error")
        self.status.emit(status)
        self.finished.emit()


class RsSpectrumWorker(QObject):
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        spectrum = SpectrumBlock(
            address=state.SPECTRUM_ADDRESS,
        )
        result = spectrum.idn()
        if not result:
            self.status.emit("Undefined Error")
            self.finished.emit()
        status = "Ok" if "FSEK" in result else "Undefined Error"
        self.status.emit(status)
        self.finished.emit()


class PrologixEthernetThread(QThread):
    status = pyqtSignal(bool)

    def run(self):
        try:
            PrologixGPIBEthernet(host=state.PROLOGIX_IP)
            logger.info(
                f"[{self.__class__.__name__}.run] Prologix Ethernet Initialized"
            )
            self.status.emit(True)
        except:
            logger.error(
                f"[{self.__class__.__name__}.run] Prologix Ethernet unable to initialize"
            )
            self.status.emit(False)

        self.finished.emit()


class KeithleyOutputWorker(QObject):
    finished = pyqtSignal()
    keithley_state = pyqtSignal(str)

    def run(self):
        keithley = KeithleyBlock(address=state.KEITHLEY_ADDRESS)
        keithley.set_output_state(state=state.KEITHLEY_OUTPUT_STATE)
        keithley_state = keithley.get_output_state()
        self.keithley_state.emit(keithley_state)
        self.finished.emit()


class NRXBlockWorker(QObject):
    finished = pyqtSignal()
    status = pyqtSignal(str)

    def run(self):
        block = NRXBlock(
            ip=state.NRX_IP,
            aperture_time=state.NRX_APER_TIME,
        )
        result = block.test()
        block.close()
        self.status.emit(state.NRX_TEST_MAP.get(result, "Error"))
        self.finished.emit()


class SetUpTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.createGroupNRX()
        self.createGroupPrologixEthernet()
        self.createGroupKeithley()
        self.createGroupRsSpectrumAnalyzer()
        self.layout.addWidget(self.groupNRX)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.groupPrologixEthernet)
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
        self.nrxIPLabel.setText("IP address:")
        self.nrxIP = QLineEdit(self)
        self.nrxIP.setText(state.NRX_IP)

        self.nrxAperTimeLabel = QLabel(self)
        self.nrxAperTimeLabel.setText("Averaging time, s:")
        self.nrxAperTime = QDoubleSpinBox(self)
        self.nrxAperTime.setDecimals(5)
        self.nrxAperTime.setRange(1e-5, 1000)
        self.nrxAperTime.setValue(state.NRX_APER_TIME)

        self.nrxStatusLabel = QLabel(self)
        self.nrxStatusLabel.setText("Status:")
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

    def createGroupPrologixEthernet(self):
        self.groupPrologixEthernet = QGroupBox("Prologix Ethernet config")
        self.groupPrologixEthernet.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.prologixIPAdressLabel = QLabel(self)
        self.prologixIPAdressLabel.setText("IP address:")
        self.prologixIPAdress = QLineEdit(self)
        self.prologixIPAdress.setText(state.PROLOGIX_IP)

        self.prologixEthernetStatusLabel = QLabel(self)
        self.prologixEthernetStatusLabel.setText("Status:")
        self.prologixEthernetStatus = QLabel(self)
        self.prologixEthernetStatus.setText("Prologix is not initialized yet!")

        self.btnInitPrologixEthernet = QPushButton("Initialize Prologix")
        self.btnInitPrologixEthernet.clicked.connect(self.initialize_prologix_ethernet)

        layout.addWidget(self.prologixIPAdressLabel, 1, 0)
        layout.addWidget(self.prologixIPAdress, 1, 1)
        layout.addWidget(self.prologixEthernetStatusLabel, 2, 0)
        layout.addWidget(self.prologixEthernetStatus, 2, 1)
        layout.addWidget(self.btnInitPrologixEthernet, 3, 0, 1, 2)

        self.groupPrologixEthernet.setLayout(layout)

    def createGroupKeithley(self):
        self.groupKeithley = QGroupBox("Power supply config")
        self.groupKeithley.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout = QGridLayout()

        self.keithleyAddressLabel = QLabel(self)
        self.keithleyAddressLabel.setText("GPIB address:")
        self.keithleyAddress = QDoubleSpinBox(self)
        self.keithleyAddress.setRange(0, 31)
        self.keithleyAddress.setDecimals(0)
        self.keithleyAddress.setValue(state.KEITHLEY_ADDRESS)

        self.keithleyStatusLabel = QLabel(self)
        self.keithleyStatusLabel.setText("Status:")
        self.keithleyStatus = QLabel(self)
        self.keithleyStatus.setText("Power supply is not initialized yet!")

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
        self.rsSpectrumAddressLabel.setText("GPIB address:")
        self.rsSpectrumAddress = QDoubleSpinBox(self)
        self.rsSpectrumAddress.setRange(0, 31)
        self.rsSpectrumAddress.setDecimals(0)
        self.rsSpectrumAddress.setValue(state.SPECTRUM_ADDRESS)

        self.rsSpectrumStatusLabel = QLabel(self)
        self.rsSpectrumStatusLabel.setText("Status:")
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

    def set_keithley_btn_state(self, keithley_state: str):
        text = state.KEITHLEY_OUTPUT_STATE_MAP.get(keithley_state)
        self.btnKeithleyState.setText(f"{text}")

    def set_keithley_state(self):
        self.keithley_state_thread = QThread()
        self.keithley_state_worker = KeithleyOutputWorker()

        state.KEITHLEY_OUTPUT_STATE = state.KEITHLEY_OUTPUT_STATE_MAP_REVERSE.get(
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
        self.keithley_state_worker.keithley_state.connect(self.set_keithley_btn_state)
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

        state.NRX_IP = self.nrxIP.text()
        state.NRX_APER_TIME = self.nrxAperTime.value()

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

        state.KEITHLEY_ADDRESS = int(self.keithleyAddress.value())

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

        state.SPECTRUM_ADDRESS = int(self.rsSpectrumAddress.value())

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

    def initialize_prologix_ethernet(self):
        self.prologix_ethernet_thread = PrologixEthernetThread()

        state.PROLOGIX_IP = self.prologixIPAdress.text()

        self.prologix_ethernet_thread.status.connect(self.set_prologix_ethernet_status)
        self.prologix_ethernet_thread.start()

        self.btnInitPrologixEthernet.setEnabled(False)
        self.prologix_ethernet_thread.finished.connect(
            lambda: self.btnInitPrologixEthernet.setEnabled(True)
        )

    def set_prologix_ethernet_status(self, status: bool):
        if status:
            self.prologixEthernetStatus.setText("Ok")
        else:
            self.prologixEthernetStatus.setText("Error!")
