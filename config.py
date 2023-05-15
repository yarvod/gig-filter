class Config:
    PROLOGIX_ADDRESS = 6
    KEITHLEY_ADDRESS = 22
    NRX_IP = "169.254.2.20"

    KEITHLEY_MEAS = False
    KEITHLEY_CURRENT_FROM = 0
    KEITHLEY_CURRENT_TO = 0.1
    KEITHLEY_CURRENT_POINTS = 100
    KEITHLEY_CURRENT_SET = 0
    KEITHLEY_VOLTAGE_SET = 0
    KEITHLEY_STREAM = False
    KEITHLEY_OUTPUT_STATE = "0"
    KEITHLEY_OUTPUT_STATE_MAP = dict((("0", "Off"), ("1", "On")))
    KEITHLEY_OUTPUT_STATE_MAP_REVERSE = dict((("On", "0"), ("Off", "1")))

    KEITHLEY_TEST_MAP = dict(
        (
            ("0", "Ok"),
            ("1", "Module Initialization Lost"),
            ("2", "Mainframe Initialization Lost"),
            ("3", "Module Calibration Lost"),
            ("4", "Non-volatile RAM STATE section checksum failed"),
            ("5", "Non-volatile RAM RST section checksum failed"),
            ("10", "RAM selftest"),
            ("40", "Flash write failed"),
            ("41", "Flash erase failed"),
            ("80", "Digital I/O selftest erro"),
        )
    )

    NRX_STREAM = False

    NRX_TEST_MAP = dict(
        (
            ("0", "Ok"),
            ("1", "Error"),
        )
    )
    NRX_FILTER_TIME = 0.01
    NRX_APER_TIME = 0.1


config = Config()
