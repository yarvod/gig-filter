import time

import pyvisa

from utils.logger import logger


def exception(func):
    """Simple function exception decorator"""

    def wrapper(*args, **kwargs):
        for attempt in range(1, 5):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"[Attempt {attempt}][{func.__qualname__}] {e}")

    return wrapper


def visa_exception(func):
    """Visa function exception decorator"""

    def wrapper(*args, **kwargs):
        for attempt in range(1, 5):
            if attempt > 1:
                time.sleep(0.2)
            try:
                return func(*args, **kwargs)
            except (
                pyvisa.errors.VisaIOError,
                TypeError,
                ValueError,
                AttributeError,
            ) as e:
                logger.error(f"[Attempt {attempt}][{func.__qualname__}] {e}")

    return wrapper
