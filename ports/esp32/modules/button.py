from utime import ticks_ms, ticks_diff


class Button():
    def __init__(self, pin):
        self.pin = pin
        self.t = None

    def is_pressed(self):
        if self.pin.value() == 0:
            if self.t == None:
                self.t = ticks_ms()
            elif ticks_diff(ticks_ms(), self.t) >= 500:
                return 2
            elif ticks_diff(ticks_ms(), self.t) >= 100:
                return 1
        else:
            self.t = None
        return 0
