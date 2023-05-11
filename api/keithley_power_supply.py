import sys

import pyvisa

from config import config
from utils.decorators import visa_exception


class KeithleyBlock:

    def __init__(self, address: str = config.KEITHLEY_ADDRESS):
        self.address = address
        resource_manager = pyvisa.ResourceManager()
        self.instr = resource_manager.open_resource(self.address)

    @visa_exception
    def idn(self):
        return self.instr.query("*IDN?")

    @visa_exception
    def reset(self):
        self.instr.write("*RST")

    def test(self):
        """Test function: 0 - Good, 1 - Bad"""
        return self.instr.query("*TST?").strip()

    @visa_exception
    def set_output_state(self, state: int):
        """Output State 0 - off, 1 - on"""
        self.instr.write(f"OUTPUT {state}")

    @visa_exception
    def get_output_state(self):
        """Output State 0 - off, 1 - on"""
        return self.instr.query(f"OUTPUT?").strip()

    @visa_exception
    def get_current(self):
        return float(self.instr.query("MEAS:CURR?"))

    @visa_exception
    def get_setted_current(self):
        return float(self.instr.query("SOUR:CURR?"))

    @visa_exception
    def get_voltage(self):
        return float(self.instr.query("MEAS:VOLT?"))

    @visa_exception
    def set_current(self, current: float) -> float:
        self.instr.write(f"SOUR:CURR {current}A")
        return float(self.instr.query(f"SOUR:CURR?"))

    def close(self):
        self.instr.close()


if __name__ == '__main__':
    block = KeithleyBlock()
    res = block.test()
    print(f'res {res}')
    print(config.KEITHLEY_TEST_MAP[res])
    print(block.get_output_state())
    print(block.get_current())
    print(block.get_voltage())
