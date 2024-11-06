# Test machine.PWM, frequncy and duty cycle (using machine.time_hardware_pulse_us).
#
# IMPORTANT: This test requires hardware connections: the PWM-output and pulse-input
# pins must be wired together.

import sys, time

try:
    from machine import time_hardware_pulse_us, Pin, PWM
except ImportError:
    print("SKIP")
    raise SystemExit

FREQS1 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
FREQS2 = (50, 100, 500, 1_000, 2_000, 5_000, 10_000)
FREQS3 = (100_000, 1_000_000, 10_000_000, 20_000_000, 40_000_000)
FREQS = FREQS1 + FREQS2 + FREQS3
FREQS = FREQS2

print("Test frequencies:", FREQS)

DUTY_MAX = 65536
DUTY_LEVELS = 8 # 4 # 16 #

freq_margin_per_thousand = 0
duty_margin_per_thousand = 0
timing_margin_us = 5

# Configure pins based on the target.
if "esp32" in sys.platform:
    pwm_pin = 26 # 4 # 2 #
    pulse_pin = 27 # 5 # 2 #
    freq_margin_per_thousand = 2
    duty_margin_per_thousand = 1
    timing_margin_us = 20
elif "esp8266" in sys.platform:
    pwm_pin = 4
    pulse_pin = 5
    duty_margin_per_thousand = 3
    timing_margin_us = 50
elif "mimxrt" in sys.platform:
    pwm_pin = "D0"
    pulse_pin = "D1"
elif "rp2" in sys.platform:
    pwm_pin = "GPIO0"
    pulse_pin = "GPIO1"
elif "samd" in sys.platform:
    pwm_pin = "D0"
    pulse_pin = "D1"
else:
    print("Please add support for this test on this platform.")
    raise SystemExit


def test_freq_duty(pulse_in, pwm, freq, duty_u16):
    print("freq= {:<8} duty_u16 = {:<5} = {:6.2f}% :".format(freq, duty_u16, duty_u16 * 100 / DUTY_MAX), end="")

    # Keep values ​​stable during calculations and prints
    pwm_freq = pwm.freq()
    pwm_duty_u16 = pwm.duty_u16()
    # Check configured freq/duty_u16 is within error bound.
    freq_error = abs(pwm_freq - freq) * 1000 // freq
    duty_error = abs(pwm_duty_u16 - duty_u16) * 1000 // (duty_u16 or 1)
    print("", freq_error <= freq_margin_per_thousand or (freq, pwm_freq), end="")
    print("", duty_error <= duty_margin_per_thousand or (duty_u16, pwm_duty_u16), end="")
    print(" :", end="")

    # Calculate expected timing.
    expected_total_us = 1_000_000 // freq
    expected_high_us = expected_total_us * duty_u16 // DUTY_MAX
    expected_low_us = expected_total_us - expected_high_us
    expected_us = (expected_low_us, expected_high_us)
    timeout = 2 * expected_total_us

    if duty_u16 == 0 or duty_u16 == DUTY_MAX:
        # Expect a constant output level.
        no_pulse = (
            time_hardware_pulse_us(pulse_in, 0, timeout) < 0 and time_hardware_pulse_us(pulse_in, 1, timeout) < 0
        )
        if expected_high_us == 0:
            # Expect a constant low level.
            print("", 0, no_pulse and pulse_in() == 0)
        else:
            # Expect a constant high level.
            print("       ", 1, no_pulse and pulse_in() == 1)
    else:
        # Test timing of low and high pulse.
        n_averaging = 10
        for level in (0, 1):
            t = 0
            for _ in range(n_averaging):
                t += time_hardware_pulse_us(pulse_in, level, timeout)
            t //= n_averaging
            expected = expected_us[level]
            print("", level, abs(t - expected) <= timing_margin_us or (expected, t), end="")
        print()


def test():
    pulse_in = Pin(pulse_pin, Pin.IN)
    pwm = PWM(pwm_pin)

    for freq in FREQS:
        pwm.freq(freq)
        for duty in range(0, DUTY_LEVELS + 1):
            duty_u16 = DUTY_MAX * duty // DUTY_LEVELS
            if 0 and sys.platform == "esp32":
                # TODO why is this bit needed to get it working on esp32?
                # Note: do not need in #10854
                import time

                pwm.init(freq=freq, duty_u16=duty_u16)
                time.sleep(0.1)
            pwm.duty_u16(duty_u16)
            if sys.platform == "esp32":
                 time.sleep(1/freq) # wait for duty stabilization during one period of the PWM signal
            test_freq_duty(pulse_in, pwm, freq, duty_u16)
        print()
    pwm.deinit()


test()