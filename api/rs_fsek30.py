from api.prologixUsb import PrologixGPIBUsb
from config import config
from utils.decorators import exception


class SpectrumBlock:
    def __init__(
        self,
        port_number: int = config.PROLOGIX_ADDRESS,
        address: int = config.SPECTRUM_ADDRESS,
    ):
        self.address = address
        self.instr = PrologixGPIBUsb(port_number)

    @exception
    def close(self):
        self.instr.close()

    @exception
    def idn(self):
        return self.instr.query("*IDN?", self.address)

    @exception
    def reset(self):
        self.instr.write("*RST", self.address)

    @exception
    def test(self):
        """Test function: 0 - Good, 1 - Bad"""
        return self.instr.query("*TST?", self.address).strip()

    def peak_search(self):
        return self.instr.query(f"CALC:MARK:MAX", self.address)

    @exception
    def get_peak_freq(self):
        return float(self.instr.query(f"CALC:MARK:X?", self.address))

    @exception
    def get_peak_power(self):
        return float(self.instr.query(f"CALC:MARK:Y?", self.address))


if __name__ == "__main__":
    block = SpectrumBlock()
    print(block.idn())
    print("peak", block.peak_search())
    print("pow", block.get_peak_power())
    print("freq", block.get_peak_freq())
