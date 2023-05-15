import serial
import sys
import time

from utils.logger import logger


def main():
    gp = PrologixGPIBUsb(int(sys.argv[1]), 22)
    gp.scan(silence=False)

    print(gp.query("*IDN?"))
    return


class PrologixGPIBUsb:
    resource = None
    opened = False
    eq_list = []

    def __init__(self, port_number: int, address: int):
        self.port_number = port_number
        if (self.resource is None) or (not self.resource.isOpen()):
            self.opened = self.init_gpib_card()
        self.eq_addr = address
        return

    def scan(self, silence=True):
        self.eq_list = self.scan_eq(self.resource, silence=silence)
        return

    def lock(self):
        self.resource.write(("++addr {}\n".format(self.eq_addr)).encode())
        self.resource.write("++llo\n".encode())
        return

    def reset(self):
        self.resource.write("++rst\n".encode())
        time.sleep(3)
        self.init_cfg()
        return

    def init_cfg(self):
        self.resource.write("++savecfg 0\n".encode())
        # 3 methods: LF only, EOI only and LF+EOI.
        self.resource.write(
            "++eos 2\n".encode()
        )  # LF+EOI, some Anritsu instruments require this.
        # self.port.write('++eos 3\n'.encode()) # None (EOI only), hardware only per standard.
        self.resource.write("++mode 1\n".encode())
        self.resource.write("++eoi 1\n".encode())
        self.resource.write("++eot_char 13\n".encode())
        self.resource.write("++eot_enable 1\n".encode())
        self.resource.write("++auto 0\n".encode())
        self.resource.write("++read_tmo_ms 300\n".encode())
        return

    def find_model_gpib(self):
        model = ""
        eq_info = self.query("*IDN?")
        if eq_info != "":
            model = eq_info.split(",")[1].strip()
        return model

    def command(self, cmd, delay=0.0):
        self.resource.write(("++addr {}\n".format(self.eq_addr)).encode())
        self.resource.write((cmd + "\n").encode())
        if delay != 0.0:
            time.sleep(delay)
        return

    def write(self, cmd: str, delay: float = 0.0):
        return self.command(cmd, delay)

    def query(self, cmd, delay=0.1):
        self.command(cmd, delay)
        time.sleep(delay)
        self.resource.write("++read eoi\n".encode())
        ans = (self.resource.readline().decode()).strip()
        return ans

    def init_gpib_card(self):
        try:
            self.resource = serial.Serial(
                "COM" + "{}".format(self.port_number), 115200, timeout=0.5
            )
            self.resource.baudrate = self.resource.BAUDRATES[-1]
        except serial.SerialException as e:
            logger.error(f"[{self.__class__.__name__}.init_gpib_card] {e}")
            return False

        self.resource.write("++ver\n".encode())
        ans = self.resource.readline().decode()

        if "Prologix GPIB-USB Controller" in ans:
            self.init_cfg()
            logger.info("[{}.init_gpib_card]COM{}: {}".format(self.__class__.__name__, self.port_number, ans))
        else:
            logger.info(
                "[{}.init_gpib_card]COM{} is NOT GPIB interface. Please check port number.".format(
                    self.__class__.__name__,
                    self.port_number
                )
            )
            return False
        return True

    def gpib_release(self):
        self.command("++loc")
        return

    def port_close(self):
        self.resource.close()
        return

    def scan_eq(self, gpib_ser, silence=False):
        eq_list = []
        for eq_addr in range(1, 31):
            id_in = self.query("*IDN?", delay=0.1)
            if id_in != "":
                if not silence:
                    logger.info("Address {}:\t".format(eq_addr) + id_in)
                eq_list.append((eq_addr, id_in))
                self.gpib_release()
            else:
                if not silence:
                    logger.info("Address {}: \tnothing found.".format(eq_addr))

        return eq_list

    def add(self, eq_addr):
        id_in = self.query("*IDN?")
        if id_in != "":
            logger.info("Address {}:\t".format(eq_addr) + id_in)
            self.eq_list.append((eq_addr, id_in))
            status = True
        else:
            status = False
        return status, id_in

    def close(self):
        self.resource.close()
        logger.info(f"[{self.__class__.__name__}.close]GPIB adaptor has been reset and COM port has been closed.")
        self.opened = False
        return

    def __del__(self):
        # self.resource.write("++rst\n".encode())
        self.close()


if __name__ == "__main__":
    main()
