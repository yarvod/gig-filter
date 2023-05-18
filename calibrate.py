import time
from datetime import datetime

import numpy as np
import pandas as pd

from api.keithley_power_supply import KeithleyBlock
from api.rs_fsek30 import SpectrumBlock
from utils.logger import logger


dc_block = KeithleyBlock()
s_block = SpectrumBlock()

dc_block.set_voltage(0.3)
dc_block.set_current(0.01)


results = {
    "current_set": [],
    "current_get": [],
    "voltage_get": [],
    "power": [],
    "freq": [],
}
curr_from = 2.65e-2
curr_to = 3.7e-1
curr_num = 30
voltage = 6
freq_limit = 12e9

dc_block.set_voltage(voltage)

time_start = datetime.now()
initial_current = dc_block.get_setted_current()
for i, current in enumerate(np.linspace(curr_from, curr_to, curr_num), 1):
    current_set = dc_block.set_current(current)
    if i == 1:
        time.sleep(1)
    current_get = dc_block.get_current()
    voltage_get = dc_block.get_voltage()
    s_block.peak_search()
    time.sleep(0.1)
    power = s_block.get_peak_power()
    freq = s_block.get_peak_freq()

    if freq >= freq_limit:
        break

    results["current_set"].append(current_set)
    results["current_get"].append(current_get)
    results["voltage_get"].append(voltage_get)
    results["power"].append(power)
    results["freq"].append(freq)

    proc = round(i / curr_num * 100, 2)
    diff_time = datetime.now() - time_start
    logger.info(f"[Proc {proc} %][Time {diff_time}]")

dc_block.set_current(initial_current)

print("Input data file name:")
filename = input()
df = pd.DataFrame(data=results)
df.to_csv(f"data/{filename}", index=False)
