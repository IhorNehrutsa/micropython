# Test machine.Counter.
#
# IMPORTANT: This test requires hardware connections: the pulse-outputs and pulse-inputs
# pins must be wired together (OUT_PIN1 to INP_PIN1 and OUT_PIN2 to INP_PIN2).

import sys

try:
    from machine import Counter, Pin, PWM, Timer
except ImportError:
    print("SKIP")
    raise SystemExit


FREQ = 500_000  # 500  # Hz
FILTER_NS = 25  # ns
SECONDS = 1
MATCH = FREQ * SECONDS  # 2 seconds counting time
# MATCH = 75
MATCH_1000 = round(MATCH / 1000 * 1.5)  # match margin per thousand
if MATCH_1000 == 0:
    MATCH_1000 = 1

print("MATCH:", MATCH, "MATCH_1000:", MATCH_1000)

# Configure pins based on the target.
if "esp32" in sys.platform:
    OUT_PIN1, INP_PIN1 = 4, 5

    OUT_PIN2, INP_PIN2 = 16, 17
elif "esp8266" in sys.platform:
    #     OUT_PIN1, INP_PIN1 = 4, 5
    #
    #     OUT_PIN2, INP_PIN2 = 16, 17
    pass
elif "mimxrt" in sys.platform:
    #     OUT_PIN1 = "D0"
    #     INP_PIN1 = "D1"
    #
    #     OUT_PIN2 = "D2"
    #     INP_PIN2 = "D3"
    pass
elif "rp2" in sys.platform:
    #     OUT_PIN1 = "GPIO0"
    #     INP_PIN1 = "GPIO1"
    #
    #     OUT_PIN2 = "GPIO2"
    #     INP_PIN2 = "GPIO3"
    pass
elif "samd" in sys.platform:
    #     OUT_PIN1 = "D0"
    #     INP_PIN1 = "D1"
    #
    #     OUT_PIN2 = "D2"
    #     INP_PIN2 = "D3"
    pass
else:
    print("Please add support for this test on this platform.")
    raise SystemExit


def toggle(pin, x):
    print("toggle", pin, x, "time(s).")
    v = pin()
    for _ in range(x):
        pin(not pin())
    print("value:", pin, v, "->", pin())


is_callback = False
pwm = None
counter = None


@micropython.viper
def callback_print(counter):
    global is_callback
    is_callback = True
    print(" callback Сounter value:", counter.value(), "status:", counter.status())


@micropython.viper
def callback_pwm_deinit(counter):
    pwm.deinit()
    print(" callback pwm.deinit()")
    callback_print(counter)


@micropython.viper
def callback_timer(timer):
    pwm.deinit()
    print(" callback pwm.deinit()")
    print(" callback Сounter value:", counter.value(), "status:", counter.status())


try:
    print("Test the wire connections: out1 -> inp1.")
    out1 = Pin(OUT_PIN1, mode=Pin.OUT, value=1)
    inp1 = Pin(INP_PIN1)
    print("out1->inp1:", out1, out1(), "->", inp1, inp1())
    assert out1() == 1
    assert inp1() == 1

    out1(0)
    print("out1->inp1:", out1, out1(), "->", inp1, inp1())
    assert out1() == 0
    assert inp1() == 0
    print("Ok.")
    print()

    print("Test the wire connections: out2 -> inp2.")
    out2 = Pin(OUT_PIN2, mode=Pin.OUT, value=1)
    inp2 = Pin(INP_PIN2)
    print("out2->inp2:", out2, out2(), "->", inp2, inp2())
    assert out2() == 1
    assert inp2() == 1

    out2(0)
    print("out2->inp2:", out2, out2(), "->", inp2, inp2())
    assert out2() == 0
    assert inp2() == 0
    print("Ok.")
    print()

    #
    print("1) Test count if direction is a constant.")
    print("out1 -> inp1 is counted pulses.")
    print("Test count UP at the RISING edge.")
    # counter = Counter(0, inp1, direction=Counter.UP, edge=Counter.RISING)
    counter = Counter(0, inp1)  # the same
    print(counter, "value:", counter.value())
    assert counter.value() == 0
    toggle(out1, 1)
    print(counter, "value:", counter.value())
    assert counter.value() == 1
    toggle(out1, 1)
    print(counter, "value:", counter.value())
    assert counter.value() == 1
    print("Ok.")
    print()

    #
    print("Test count DOWN at the FALLING edge.")
    counter.init(inp1, direction=Counter.DOWN, edge=Counter.FALLING)
    print(counter, "value:", counter.value())
    assert counter.value() == 0
    toggle(out1, 1)
    print(counter, "value:", counter.value())
    assert counter.value() == 0
    toggle(out1, 1)
    print(counter, "value:", counter.value())
    assert counter.value() == -1
    print("Ok.")
    print()

    #
    counter.deinit()
    print("2) Test count if direction is a Pin().")
    print("out1 -> inp1 is counted pulses.")
    print("out2 -> inp2 is direction of counting.")
    print("Test count DOWN when direction Pin()==0 at RISING-FALLING edges.")
    counter = Counter(0, src=inp1, direction=inp2, edge=Counter.RISING | Counter.FALLING)
    out2(0)
    print("direction:", out2, out2(), "->", inp2, inp2())
    print(counter, "value:", counter.value())
    assert counter.value() == 0
    toggle(out1, 1)
    print(counter, "value:", counter.value())
    assert counter.value() == -1
    toggle(out1, 1)
    print(counter, "value:", counter.value())
    assert counter.value() == -2
    print("Ok.")
    print()
    print("Test count UP when direction Pin() == 1 at RISING-FALLING edges.")
    out2(1)
    print("direction:", out2, out2(), "->", inp2, inp2())
    toggle(out1, 1)
    print(counter, "value:", counter.value())
    assert counter.value() == -1
    toggle(out1, 1)
    print(counter, "value:", counter.value())
    assert counter.value() == 0
    print("Ok.")
    print()

    #
    print("3) Test count UP to (2^16 + 1000) and DOWN to -(2^16 + 1000) and callbacks.")
    is_callback = False
    counter.irq(handler=callback_print, trigger=Counter.IRQ_MATCH, value=1_000)
    counter.irq(handler=callback_print, trigger=Counter.IRQ_ZERO)
    assert counter.value() == 0
    print("Test count UP to (2^16 + 1000).")
    out2(1)
    toggle(out1, 2**16 + 1000)
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() == 2**16 + 1000, 2**16 + 1000
    print("Ok.")
    print()
    print("Test count DOWN to -(2^16 + 1000).")
    out2(0)
    toggle(out1, 2 * (2**16 + 1000))
    print(counter, "value:", counter.value())
    assert counter.value() == -(2**16 + 1000), -(2**16 + 1000)
    print("Ok.")
    print()

    #
    counter.deinit()
    print("4) Test count UP at inp1 Pin() & DOWN at inp2 Pin().")
    print("out1 -> inp1 is counted UP pulses.")
    print("out2 -> inp2 is counted DOWN pulses.")

    print("Test count UP on inp1 Pin() at RISING-FALLING edges.")
    counter = Counter(0, src=inp1, _src=inp2, edge=Counter.RISING | Counter.FALLING)
    is_callback = False
    counter.irq(handler=callback_print, trigger=Counter.IRQ_MATCH, value=1_000)
    counter.irq(handler=callback_print, trigger=Counter.IRQ_ZERO)
    print(counter, "value:", counter.value())
    toggle(out1, 1_100)
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() == 1_100
    print("Ok.")
    print()

    print("Test count DOWN on inp2 Pin() at RISING-FALLING edges.")
    toggle(out2, 2 * 1_100)
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() == -1_100
    print("Ok.")
    print()
    counter.irq(handler=None, trigger=Counter.IRQ_MATCH)
    counter.irq(handler=None, trigger=Counter.IRQ_ZERO)

    #
    counter.deinit()
    print("5) Test PWM counting at inp1 Pin() & direction at inp2 Pin().")
    print("Stop PWM in Timer callback.")
    print("PWM pulses: out1 -> inp1:", out1, "->", inp1)
    out2(1)
    print("direction of counting: out2 -> inp2:", out2, out2(), "->", inp2, inp2())
    print()

    pwm = PWM(out1, freq=FREQ)
    print(pwm)
    pwm.deinit()

    counter = Counter(0, src=inp1, direction=inp2)
    print(counter, "value:", counter.value())
    timer = Timer(1)
    timer.init(mode=Timer.ONE_SHOT, period=1_000 * SECONDS, callback=callback_timer)
    pwm.init(freq=FREQ)
    while counter.value() < MATCH:
        pass
    print(counter, "value:", counter.value())
    assert counter.value() >= MATCH
    assert counter.value() < MATCH + MATCH_1000
    print("Ok.")
    print()
    counter.deinit()

    #
    print("6) Test PWM counting at inp1 Pin() & direction at inp2 Pin().")
    print("Stop PWM in Counter callback.")
    print("6.1) Test count UP when direction Pin() == 1 at RISING edges.")
    out2(1)

    counter1 = Counter(1, src=inp1, direction=inp2, filter_ns=FILTER_NS)
    counter = Counter(0, src=inp1, direction=inp2, filter_ns=FILTER_NS)
    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=MATCH)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() < MATCH:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() >= MATCH
    assert counter.value() < MATCH + MATCH_1000
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=MATCH + 300)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() < MATCH + 300:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() >= MATCH + 300
    assert counter.value() < MATCH + 300 + MATCH_1000
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=MATCH + 500)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() < MATCH + 500:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() >= MATCH + 500
    assert counter.value() < MATCH + 500 + MATCH_1000
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    print("6.2) Test count DOWN when direction Pin()==0 at RISING edges.")
    out2(0)

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=MATCH + 300)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() > MATCH + 300:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() <= MATCH + 300
    assert counter.value() > MATCH + 300 - MATCH_1000
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=MATCH)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() > MATCH:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() <= MATCH
    assert counter.value() > MATCH - MATCH_1000
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=0)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() > 0:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() <= 0
    assert counter.value() > -MATCH_1000
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    counter.irq(handler=None, trigger=Counter.IRQ_MATCH)

    #     is_callback = False
    #     counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_ZERO)
    #     print(counter, "value:", counter.value())
    #     pwm.init(freq=FREQ)
    #     while counter.value() > 0:
    #         pass
    #     print(counter, "value:", counter.value())
    #     assert is_callback == True
    #     assert counter.value() <= 0
    #     assert counter.value() > -MATCH_1000
    #     assert counter.value() == counter1.value()
    #     print("Ok.")
    #     print()

    counter.irq(handler=None, trigger=Counter.IRQ_ZERO)

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=-MATCH)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() > -MATCH:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() <= -MATCH
    assert counter.value() > -(MATCH + MATCH_1000)
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=-(MATCH + 300))
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() > -(MATCH + 300):
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() <= -(MATCH + 300)
    assert counter.value() > -(MATCH + 300 + MATCH_1000)
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=-(MATCH + 500))
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() > -(MATCH + 500):
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() <= -(MATCH + 500)
    assert counter.value() > -(MATCH + 500 + MATCH_1000)
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    print("6.3) Test count UP when direction Pin() == 1 at RISING edges.")
    out2(1)

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=-(MATCH + 300))
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() < -(MATCH + 300):
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() >= -(MATCH + 300)
    assert counter.value() < -(MATCH + 300 - MATCH_1000)
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_MATCH, value=-MATCH)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() < -MATCH:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() >= -MATCH
    assert counter.value() < -(MATCH - MATCH_1000)
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    counter.irq(handler=None, trigger=Counter.IRQ_MATCH)

    is_callback = False
    counter.irq(handler=callback_pwm_deinit, trigger=Counter.IRQ_ZERO)
    print(counter, "value:", counter.value())
    pwm.init(freq=FREQ)
    while counter.value() < 0:
        pass
    print(counter, "value:", counter.value())
    assert is_callback == True
    assert counter.value() >= 0
    assert counter.value() < MATCH_1000
    assert counter.value() == counter1.value()
    print("Ok.")
    print()

    print("END.")

finally:
    print("finally:")
    try:
        pwm.deinit()
    except:
        pass
    try:
        print(counter1, end=" ")
        print("value:", counter1.value())
    except:
        pass
    try:
        counter1.deinit()
    except:
        pass
    try:
        print(counter, "value:", counter.value())
    except:
        pass
    try:
        counter.deinit()
    except:
        pass
