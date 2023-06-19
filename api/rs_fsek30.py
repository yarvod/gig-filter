from api.prologixEthernet import PrologixGPIBEthernet
from api.prologixUsb import PrologixGPIBUsb
from state import state
from utils.classes import InstrumentGPIBBlockInterface, InstrumentAdapterInterface
from utils.decorators import exception


class SpectrumBlock(InstrumentGPIBBlockInterface):
    def __init__(
        self,
        prologix_address: int = state.PROLOGIX_ADDRESS,
        prologix_ip: str = state.PROLOGIX_IP,
        address: int = state.SPECTRUM_ADDRESS,
        use_ethernet: bool = True,
    ):
        self.instr = None
        self.prologix_address = prologix_address
        self.prologix_ip = prologix_ip
        self.use_ethernet = use_ethernet
        self.address = address
        self.set_instrument_adapter()

    def set_instrument_adapter(self):
        if self.use_ethernet:
            self.instr: InstrumentAdapterInterface = PrologixGPIBEthernet(
                self.prologix_ip
            )
        else:
            self.instr: InstrumentAdapterInterface = PrologixGPIBUsb(
                self.prologix_address
            )

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
        return self.instr.write(f"CALC:MARK:MAX", self.address)

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
