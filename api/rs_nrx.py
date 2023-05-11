import time

from RsInstrument import *

from config import config
from utils.decorators import exception
from utils.logger import logger


class NRXBlock:

    def __init__(self, ip: str = config.NRX_IP):
        self.address = f"TCPIP::{ip}::INSTR"
        try:
            self.instr = RsInstrument(self.address, reset=False)
        except ResourceError as e:
            self.instr = None
            logger.error(f"[NRXBlock.__init__] Initialization error {e}")

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


if __name__ == "__main__":
    nrx = NRXBlock()
    for i in range(10):
        time.sleep(0.01)
        print(nrx.meas())
