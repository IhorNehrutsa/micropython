def off():
    try:
        print('\nSelf battery off.')
        from utime import sleep_ms
        from machine import Pin
        from esp32_ import PWR_CTRL
        sleep_ms(1000)
        Pin(PWR_CTRL, Pin.OUT, value=0)
    except Exception:
        pass


if __name__ == "__main__":
    off()
