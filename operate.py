import time
from datetime import datetime

import numpy as np
import pandas as pd

from api.keithley_power_supply import KeithleyBlock
from api.rs_nrx import NRXBlock
from utils.logger import logger

dc_block = KeithleyBlock()
dc_block.reset()
nrx_block = NRXBlock()
nrx_block.reset()

results = {
    "current_set": [],
    "current_get": [],
    "voltage_get": [],
    "power": []
}
curr_from = 2.65e-2
curr_to = 2.24e-1
curr_num = 20
time_start = datetime.now()
initial_current = dc_block.get_setted_current()
for i, current in enumerate(np.linspace(curr_from, curr_to, curr_num), 1):
    current_set = dc_block.set_current(current)
    if i == 1:
        time.sleep(2)
    time.sleep(0.5)
    current_get = dc_block.get_current()
    voltage_get = dc_block.get_voltage()
    power = nrx_block.get_power()

    results["current_set"].append(current_set)
    results["current_get"].append(current_get)
    results["voltage_get"].append(voltage_get)
    results["power"].append(power)

    proc = round(i / curr_num * 100, 2)
    diff_time = datetime.now() - time_start
    logger.info(f"[Proc {proc} %][Time {diff_time}]")

dc_block.set_current(initial_current)
dc_block.close()
nrx_block.close()

print("Input data file name:")
filename = input()
df = pd.DataFrame(data=results)
df.to_csv(f"data/{filename}", index=False)
