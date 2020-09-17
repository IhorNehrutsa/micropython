from machine import reset_cause, PWRON_RESET, HARD_RESET, WDT_RESET, DEEPSLEEP_RESET, SOFT_RESET

machine_reset_cause = {
    PWRON_RESET: "PWRON_RESET",
    HARD_RESET: "HARD_RESET",
    WDT_RESET: "WDT_RESET",
    DEEPSLEEP_RESET: "DEEPSLEEP_RESET",
    SOFT_RESET: "SOFT_RESET",
    }


def machine_reset_cause_msg(x):
    try:
        return "%d %s" % (x, machine_reset_cause[x])
    except KeyError:
        return "%d Unnown message" % (x)


# ===============================================================================
if __name__ == "__main__":
    print(machine_reset_cause_msg(reset_cause()))
    print("")
    for x in range(0, len(machine_reset_cause) + 1 + 1):
        print(machine_reset_cause_msg(x))
    #reset()
    #soft_reset()
