import pyvisa

from utils.logger import logger


class VisaGPIB:
    ADDRESS = "GPIB0::{}::INSTR"

    def __init__(self, gpib_address: int):
        self.gpib_address = gpib_address
        self.address = self.ADDRESS.format(gpib_address)
        self.resource_manager = pyvisa.ResourceManager()
        try:
            self.resource = self.resource_manager.open_resource(self.address)
        except pyvisa.errors.VisaIOError as e:
            self.resource = None
            logger.error(f"[{self.__class__.__name__}.__init__] Initialization error {e}")

    def query(self, cmd: str):
        return self.resource.query(cmd)

    def write(self, cmd: str):
        return self.resource.write(cmd)

    def close(self):
        return self.resource.close()

    @staticmethod
    def scan():
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        logger.info(f"[VisaGPIB.scan_gpib] all devices {resources}")
        for i, resource in enumerate(resources):
            logger.info(f"[VisaGPIB.scan_gpib][Check {i + 1}] Check {resource}")
            try:
                rm.open_resource(resource)
                logger.info(
                    f"[VisaGPIB.scan_gpib][Check {i + 1}][Success check] resource {resource} available"
                )
            except pyvisa.errors.VisaIOError as e:
                logger.error(
                    f"[VisaGPIB.scan_gpib][Check {i + 1}][Check Error] resource {resource} with error {e}"
                )


if __name__ == "__main__":
    import sys

    instr = VisaGPIB(int(sys.argv[1]))
    instr.scan()
