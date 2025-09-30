from utime import ticks_diff, ticks_us, sleep_us
from machine import Pin


class Stepper():
    def __init__(self, name, pin_step, pin_dir, freq=5_000, reverse_direction=0, max_limit=None, min_limit=None):
        self.name = name

        if isinstance(pin_step, Pin):
            self.pin_step = pin_step
        else:
            self.pin_step = Pin(pin_step, Pin.OUT)

        if isinstance(pin_dir, Pin):
            self.pin_dir = pin_dir
        else:
            self.pin_dir = Pin(pin_dir, Pin.OUT)

        self.stepper_set_freq(freq)

        self.reverse_direction = reverse_direction  # развернуть направление вращения мотора

        self.steps_max_limit = max_limit  # физические механические ограничения конструкции
        self.steps_min_limit = min_limit

        self._steps_now = 0
        self._steps_target = 0

        self._direction = 0  # (-1, 0, 1) текущее направление вращения, устанавливается в dir()
        self._us_prev_step = 0

    def __repr__(self):
        return f"Stepper('{self.name}', pin_step={self.pin_step}, pin_dir={self.pin_dir}, freq={self._freq}, reverse_direction={self._reverse_direction}, steps_max_limit={self.steps_max_limit}, steps_min_limit={self.steps_min_limit})"

    # -----------------------------------------------------------------------
    @property
    def reverse_direction(self):
        return self._reverse_direction

    #@micropython.native
    @reverse_direction.setter
    def reverse_direction(self, reverse_direction:int):
        self._reverse_direction = 1 if bool(reverse_direction) else 0

    # -----------------------------------------------------------------------
    def stepper_set_freq(self, freq):
        # частота в Гц и период следования импульсов в мкс
        self._freq = freq if freq > 0 else 1

        self.us_step_period = round(1_000_000 / self._freq)
        #print(f'Stepper.stepper_set_freq(): self._freq={self._freq}, self.us_step_period={self.us_step_period}')

    #@micropython.native
    @property
    def freq(self):
        #print('Stepper.freq.property')
        return self._freq

    #@micropython.native
    @freq.setter
    def freq(self, freq):
        #print('Stepper.freq.setter')
        self.stepper_set_freq(freq)

    # -----------------------------------------------------------------------
    #@micropython.native
    @property
    def steps_now(self) -> int:
        return self._steps_now

    #@micropython.native
    @property
    def steps_target(self) -> int:
        return self._steps_target

    #@micropython.native
    @steps_target.setter
    def steps_target(self, steps_target):
        # Set the target position that will be executed in the main loop
        #print(f"Stepper():steps_target.setter({steps_target})")
        if self.steps_max_limit is not None:
            if steps_target > self.steps_max_limit:
                steps_target = self.steps_max_limit
        if self.steps_min_limit is not None:
            if steps_target < self.steps_min_limit:
                steps_target = self.steps_min_limit
        self._steps_target = steps_target

    # -----------------------------------------------------------------------
    @property
    def direction(self) -> int:
        return self._direction

    #@micropython.native
    @direction.setter
    def direction(self, delta:int):
        if delta > 0:
            self._direction = 1
            self.pin_dir(1 ^ self._reverse_direction)
        elif delta < 0:
            self._direction = -1
            self.pin_dir(0 ^ self._reverse_direction)
        else:
            self._direction = 0
        #print(f'{self.name} Set direction:delta={delta} to self._direction={self._direction} with self._reverse_direction={self._reverse_direction} self.pin_dir()={self.pin_dir()}')

    def set_dir(self, delta:int):
        if delta > 0:
            self.pin_dir(1 ^ self._reverse_direction)
        elif delta < 0:
            self.pin_dir(0 ^ self._reverse_direction)

    def stop_pulses(self):
        self._direction = 0
    # -----------------------------------------------------------------------
#     #@micropython.native
#     def single_step(self, step_pulse_us:int=5): # длительность импульса в мкс: 7.5us при 5us  и  12.5us при 10us
#         # Execute one step
#         if self._direction != 0:  # 24.96kHz
#             self.pin_step(0)  # 26.21kHz
#             #self.pin_step(not self.pin_step())  # 19.48kHz
#             #self.pin_step.init(mode=Pin.OUT, value=0)  # 14.39kHz
#             #pin_step = Pin(self.pin_step, mode=Pin.OUT, value=0)  # 14.61kHz
#             sleep_us(step_pulse_us)
#             #sleep_ms(1)
#             #pin_step(1)  # 14.61kHz
#             #self.pin_step(1)  # 14.39kHz
#             #self.pin_step(not self.pin_step())  # 19.48kHz
#             self.pin_step(1)  # 26.21kHz
#             self._steps_now += self._direction
#
#     #@micropython.native
#     def run_single_step(self):
#         # Check the step period and run one step
#         diff = ticks_diff(t:=ticks_us(), self._us_prev_step)
#         if (diff >= self.us_step_period) or (diff <= 0):
#             self._us_prev_step = t
#             self.single_step()
#         # 7.64kHz
#
#     def run_steps(self, steps):  # 7.45kHz
#         print(f"Run {steps} steps")
#         self.direction = steps
#         steps = abs(steps)
#         while (steps > 0):
#             steps -= 1
#             self.run_single_step()

    ### #@micropython.native # 8.03kHz - мешает прервать по Ctrl-C
    def run_steps(self, steps:int):  # 8.03kHz
        steps = round(steps)
        print(f"{self.name}.run_steps({steps})")
        self.direction = steps
        self._steps_now += steps
        steps = abs(steps) * 2
        us_step_period = self.us_step_period // 2
        if us_step_period <= 0:
            us_step_period = 1
        #elif us_step_period >= 5_000:
        #    us_step_period = 5_000  # 100Hz
        pin_step_value = self.pin_step()
        while ((steps > 0) and (self._direction != 0)):
            diff = ticks_diff(t:=ticks_us(), self._us_prev_step)
            if (diff >= us_step_period) or (diff <= 0):
                self._us_prev_step = t
                self.pin_step(pin_step_value := not pin_step_value)
                steps -= 1

    def go(self, steps_target = None):
        if steps_target is not None:
            self.steps_target = steps_target
        print(f'{self.name}.go({self.steps_target})')
        self.run_steps(self._steps_target - self._steps_now)

    #@micropython.native
    def is_ready(self) -> bool:
        return self._steps_target == self._steps_now
