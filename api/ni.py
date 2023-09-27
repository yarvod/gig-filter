import json
import time

import requests

from api.rs_fsek30 import SpectrumBlock
from store.state import state


class NiYIGManager:
    def __init__(
        self,
        host: str = state.NI_IP,
    ):
        self.url = f"{state.NI_PREFIX}{host}"
        self.headers = {"Content-Type": "application/json"}

    def test(self) -> bool:
        response = requests.get(self.url, headers=self.headers)
        return response.status_code == 200

    def get_devices(self):
        url = f"{self.url}/devices/"
        response = requests.get(url, headers=self.headers)
        return response

    def start_task(self, device: str = "Dev1"):
        url = f"{self.url}/devices/{device}/start"
        response = requests.post(url, headers=self.headers)
        return response

    def stop_task(self, device: str = "Dev1"):
        url = f"{self.url}/devices/{device}/stop"
        response = requests.post(url, headers=self.headers)
        return response

    def close_task(self, device: str = "Dev1"):
        url = f"{self.url}/devices/{device}/close"
        response = requests.post(url, headers=self.headers)
        return response

    def write_task(self, value: int, device: str = "Dev1"):
        value = int(value)
        url = f"{self.url}/devices/{device}/write"
        response = requests.post(
            url, data=json.dumps({"value": value}), headers=self.headers
        )
        return response

    def device_reset(self, device: str = "Dev1"):
        url = f"{self.url}/devices/{device}/reset"
        response = requests.post(url, headers=self.headers)
        return response


if __name__ == "__main__":
    url = "http://169.254.0.86/devices/Dev1/write"
    s_block = SpectrumBlock(
        prologix_ip=state.PROLOGIX_IP, address=state.SPECTRUM_ADDRESS
    )
    data = {"power": [], "freq": [], "point": []}
    try:
        for i in range(4096):
            time.sleep(state.CALIBRATION_STEP_DELAY)
            if i == 0:
                time.sleep(0.4)
            requests.post(url, data=json.dumps({"value": i}))
            s_block.peak_search()
            power = s_block.get_peak_power()
            freq = s_block.get_peak_freq()
            data["point"].append(i)
            data["power"].append(power)
            data["freq"].append(freq)
            print(f"[STEP {i}/4095][FREQ {round(freq/1e9, 5)}]")
    except KeyboardInterrupt:
        pass

    with open("calibration_digital.json", "w") as f:
        json.dump(data, f)
