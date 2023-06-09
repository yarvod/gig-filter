from utils.logger import logger


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            logger.info(
                f"[{cls.__name__}.__call__] Class is not initialized yet, initializing ..."
            )
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        logger.info(f"[{cls.__name__}.__call__] Class already initialized!")
        return cls._instances[cls]


class InstrumentGPIBBlockInterface:
    def set_instrument_adapter(self):
        raise NotImplementedError

    def idn(self, *args, **kwargs):
        raise NotImplementedError

    def close(self, *args, **kwargs):
        raise NotImplementedError


class InstrumentAdapterInterface:
    """
    This is the base interface for Instrument adapter
    """

    def read(self, *args, **kwargs):
        raise NotImplementedError

    def query(self, *args, **kwargs):
        raise NotImplementedError

    def write(self, *args, **kwargs):
        raise NotImplementedError

    def connect(self, *args, **kwargs):
        raise NotImplementedError

    def close(self, *args, **kwargs):
        raise NotImplementedError
