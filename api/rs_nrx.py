from RsInstrument import *

from config import config
from utils.decorators import exception
from utils.logger import logger


class NRXBlock:
    def __init__(
        self,
        ip: str = config.NRX_IP,
        avg_time: float = config.NRX_FILTER_TIME,
        aper_time: float = config.NRX_APER_TIME,
    ):
        self.address = f"TCPIP::{ip}::INSTR"
        self.instr = None

        self.open_instrument()
        self.set_awaiting_time(avg_time)
        self.set_aperture_time(aper_time)

    @exception
    def open_instrument(self):
        self.instr = RsInstrument(self.address, reset=False)

    @exception
    def close(self):
        self.instr.close()

    @exception
    def reset(self):
        self.instr.write("*RST")

    def configure(self):
        self.instr.write("CONF1 -50,3,(@1)")

    @exception
    def idn(self):
        return self.instr.query("*IDN?")

    @exception
    def test(self):
        return self.instr.query("*TST?")

    @exception
    def get_power(self):
        return self.instr.query_float("READ?")

    @exception
    def meas(self):
        return self.instr.query_float("MEAS? -50,3,(@1)")

    @exception
    def get_conf(self):
        return self.instr.query("CONF?")

    @exception
    def fetch(self):
        return self.instr.query_float("FETCH?")

    @exception
    def set_lower_limit(self, limit: float):
        self.instr.write(f"CALCulate1:LIMit1:LOWer:DATA {limit}")

    @exception
    def set_upper_limit(self, limit: float):
        self.instr.write(f"CALCulate1:LIMit1:UPPer:DATA {limit}")

    @exception
    def set_awaiting_time(self, time: float = config.NRX_FILTER_TIME):
        """
        :param time: seconds
        :return:
        """
        self.instr.write(f"CALCulate:CHANnel:AVERage:COUNt:AUTO:MTIMe {time}")

    @exception
    def set_aperture_time(self, time: float = config.NRX_APER_TIME):
        """
        :param time: seconds
        :return:
        """
        self.instr.write(f"CALC:APER {time}")


if __name__ == "__main__":
    nrx = NRXBlock()
    nrx.instr.write(f"CALC:APER 0.2")
