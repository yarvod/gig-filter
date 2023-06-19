from api.prologixEthernet import PrologixGPIBEthernet
from api.prologixUsb import PrologixGPIBUsb
from state import state
from utils.classes import InstrumentAdapterInterface, InstrumentGPIBBlockInterface
from utils.decorators import visa_exception


class KeithleyBlock(InstrumentGPIBBlockInterface):
    def __init__(
        self,
        prologix_address: int = state.PROLOGIX_ADDRESS,
        prologix_ip: str = state.PROLOGIX_IP,
        address: int = state.KEITHLEY_ADDRESS,
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

    @visa_exception
    def idn(self):
        return self.instr.query("*IDN?", self.address)

    @visa_exception
    def reset(self):
        self.instr.write("*RST", self.address)

    @visa_exception
    def test(self):
        """Test function: 0 - Good, 1 - Bad"""
        return self.instr.query("*TST?", self.address).strip()

    @visa_exception
    def set_output_state(self, state: int):
        """Output State 0 - off, 1 - on"""
        self.instr.write(f"OUTPUT {state}", self.address)

    @visa_exception
    def get_output_state(self):
        """Output State 0 - off, 1 - on"""
        return self.instr.query(f"OUTPUT?", self.address).strip()

    @visa_exception
    def get_current(self):
        return float(self.instr.query("MEAS:CURR?", self.address))

    @visa_exception
    def get_setted_current(self):
        return float(self.instr.query("SOUR:CURR?", self.address))

    @visa_exception
    def get_voltage(self):
        return float(self.instr.query("MEAS:VOLT?", self.address))

    @visa_exception
    def set_current(self, current: float) -> float:
        self.instr.write(f"SOUR:CURR {current}A", self.address)
        return float(self.instr.query(f"SOUR:CURR?", self.address))

    @visa_exception
    def set_voltage(self, voltage: float) -> float:
        self.instr.write(f"SOUR:VOLT {voltage}V", self.address)
        return float(self.instr.query(f"SOUR:VOLT?", self.address))

    @visa_exception
    def close(self):
        self.instr.close()


if __name__ == "__main__":
    block = KeithleyBlock()
    res = block.test()
    print(f"res {res}")
    print(state.KEITHLEY_TEST_MAP[res])
    print(block.get_output_state())
    print(block.get_current())
    print(block.get_voltage())
