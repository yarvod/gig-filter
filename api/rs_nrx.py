from RsInstrument import *

from config import config
from utils.decorators import exception


class NRXBlock:

    def __init__(self, ip: str = config.NRX_IP):
        self.address = f"TCPIP::{ip}::INSTR"
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


if __name__ == "__main__":
    nrx = NRXBlock()
    nrx.reset()
    # print(nrx.idn())
    # nrx.configure()
    print(nrx.get_power())
    print(nrx.get_power())
