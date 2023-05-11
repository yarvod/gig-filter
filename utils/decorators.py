import pyvisa

from utils.logger import logger


def exception(func):
    """Simple function exception decorator"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"[{func.__qualname__}] {e}")

    return wrapper


def visa_exception(func):
    """Visa function exception decorator"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (pyvisa.errors.VisaIOError, TypeError, ValueError, AttributeError) as e:
            logger.error(f"[{func.__qualname__}] {e}")

    return wrapper
