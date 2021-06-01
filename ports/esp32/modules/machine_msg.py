from machine import PWRON_RESET, HARD_RESET, WDT_RESET, DEEPSLEEP_RESET, SOFT_RESET, BROWNOUT_RESET

_MACHINE_RESET_CAUSE = {
    PWRON_RESET: "PWRON_RESET",
    HARD_RESET: "HARD_RESET",
    WDT_RESET: "WDT_RESET",
    DEEPSLEEP_RESET: "DEEPSLEEP_RESET",
    SOFT_RESET: "SOFT_RESET",
    BROWNOUT_RESET: "BROWNOUT_RESET",
    }


@micropython.native
def machine_reset_cause(x: int):
    try:
        return "{}:{}".format(x, _MACHINE_RESET_CAUSE[x])
    except KeyError:
        return "_MACHINE_RESET_CAUSE[{}]-unnown message".format(x)
