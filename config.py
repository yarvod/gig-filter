class Config:
    KEITHLEY_ADDRESS = "GPIB0::22::INSTR"
    NRX_IP = "169.254.2.20"

    KEITHLEY_TEST_MAP = dict(
        (
            ("0", "Ok"),
            ("1", "Error"),
        )
    )

    NRX_TEST_MAP = dict(
        (
            (None, "Ok"),
            ("0", "Ok"),
            ("1", "Error"),
        )
    )


config = Config()
