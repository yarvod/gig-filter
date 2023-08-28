import os


class State:
    # Base
    BASE_DIR = os.getcwd()
    # Icons
    WINDOW_ICON = os.path.join(BASE_DIR, "assets", "logo_small.ico")
    UP_ARROW = os.path.join(BASE_DIR, "assets", "up-arrow.png")
    DOWN_ARROW = os.path.join(BASE_DIR, "assets", "down-arrow.png")
    # Instruments
    PROLOGIX_ADDRESS = 6
    KEITHLEY_ADDRESS = 22
    NRX_IP = "169.254.2.20"
    NRX_STREAM_THREAD = False
    NRX_STREAM_PLOT_GRAPH = False
    NRX_STREAM_GRAPH_POINTS = 150
    PROLOGIX_IP = "169.254.156.103"
    NI_PREFIX = "http://"
    NI_IP = "169.254.0.86"

    NI_FREQ_TO = 13
    NI_FREQ_FROM = 3
    NI_FREQ_POINTS = 300
    NI_STABILITY_MEAS = False
    DIGITAL_YIG_FREQ = 8
    NRX_POINTS = 20

    SPECTRUM_ADDRESS = 20

    KEITHLEY_MEAS = False
    CALIBRATION_MEAS = False
    KEITHLEY_FREQ_FROM = 1
    KEITHLEY_FREQ_TO = 6
    KEITHLEY_CURRENT_FROM = 0
    KEITHLEY_CURRENT_TO = 0.1
    KEITHLEY_CURRENT_POINTS = 100
    KEITHLEY_CURRENT_SET = 0
    KEITHLEY_VOLTAGE_SET = 0
    KEITHLEY_STREAM_THREAD = False
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
    NRX_APER_TIME = 0.05

    CALIBRATION_CURR_2_FREQ = [3.49015508e10, 1.14176903e08]
    CALIBRATION_FREQ_2_CURR = [2.86513427e-11, -3.26694024e-03]
    CALIBRATION_FILE = os.path.join(os.getcwd(), "calibration.csv")
    CALIBRATION_STEP_DELAY = 0.1

    CALIBRATION_DIGITAL_POINT_2_FREQ = [2478826.8559771227, 2937630021.5301304]
    CALIBRATION_DIGITAL_FREQ_2_POINT = [4.03405867562004e-07, -1185.002515827086]


state = State()
