from gc import collect
from machine import Pin, PWM, Counter
from utime import sleep_us, ticks_us, ticks_diff

from esp32_ import *
from stepper import Stepper
from stepper_angle import StepperAngle

collect()

ANGLE_PRECISION = 0.1


class StepMotorAccel(StepperAngle):
    def __init__(self, name, pin_step, pin_dir, freq=1000, reverse_direction=0, max_limit=180, min_limit=-180, steps_per_rev=1, angle_now_func=None, accel=None, counter=-1):
        super().__init__(name, pin_step, pin_dir, freq, reverse_direction, max_limit, min_limit, steps_per_rev)

        self.angle_now_func = angle_now_func  # external function
        self.accel = accel
        self.reverse_direction = bool(reverse_direction)

        ### 1
        if isinstance(counter, Counter):
            self.counter = counter
        else:
            self.counter = Counter(counter, src=self.pin_step, direction=self.pin_dir) #  , invert=reverse_direction)
        self.correct_counter()

        ### 2
        self.pwm = PWM(self.pin_step, freq=freq, duty_u16=0)  # 0%
        #self.us_step_period = 0  # round(1_000_000 / freq)

        self._last_time = ticks_us()

        self.angle_precision = ANGLE_PRECISION

        #print(self.__repr__())

        self.__angle_now = 0
        
        self.parking_position = None

    def __repr__(self):
        return f'StepMotorAccel(angle_now_func={self.angle_now_func}, accel={self.accel}):Counter({self.counter}):' + super().__repr__()

    def info(self):
        return f'StepMotorAccel: {self.name} freq={self.freq()}, duty_u16={self.pwm.duty_u16()}'

    def deinit(self):
        try:
            self.pwm.deinit()
            self.pwm = None
        except:
            self.pwm = None
            pass
        try:
            self.counter.deinit()
        except:
            pass

    def correct_counter(self):
        self.counter.value(-self.steps_now)
        pass

    # -----------------------------------------------------------------------
    @property
    def steps_counter(self) -> int:
        return -self.counter.get_value() if self.reverse_direction else self.counter.get_value()

    @property
    def angle_counter(self):
        return round(self.steps_to_angle(self.steps_counter), 2)

    #------------------------------------------------------------------------------------------
    def freq(self):
        if self.pwm is None:
            return 0
        if self.pwm.duty_u16() == 0:
            return 0
        else:
            return self.pwm.freq()

    @property
    def rps(self):
        return self.f_to_rps(self.freq())

    @property
    def rpm(self):
        return self.f_to_rpm(self.freq())

    #------------------------------------------------------------------------------------------
    @property
    def rps_high(self):
        return self.f_to_rps(self.accel.max_output)

    @rps_high.setter
    def rps_high(self, rps):
        self.accel.max_output = round(self.rps_to_f(rps))

    @property
    def rpm_high(self):
        return self.f_to_rpm(self.accel.max_output)

    @rpm_high.setter
    def rpm_high(self, rpm):
        self.accel.max_output = round(self.rpm_to_f(rpm))

    @property
    def rps_low(self):
        return self.f_to_rps(self.accel.min_output)

    @rps_low.setter
    def rps_low(self, rps):
        self.accel.min_output = round(self.rps_to_f(rps))

    @property
    def rpm_low(self):
        return self.f_to_rpm(self.accel.min_output)

    @rpm_low.setter
    def rpm_low(self, rpm):
        self.accel.min_output = round(self.rpm_to_f(rpm))

    @property
    def angle_now(self):
        return self.angle_now_func()

    @property
    def steps_now(self):
        return self.angle_to_steps(self.angle_now_func())

    def set0(self):
        self.offset = self.angle_now_func()
        self.angle_target = 0

    #------------------------------------------------------------------------------------------
    def start_pulses(self, angle_delta):

        if self.accel.setpoint != self.angle_target:
            self.accel.setpoint = self.angle_target
            self.accel.startpoint = self.angle_now
        now = ticks_us()
        dt = ticks_diff(now, self._last_time)
        self._last_time = now
        if dt <= 0:
            dt = 1e-16
        else:
            dt /= 1_000_000
#         freq = int(round(self.accel(self.angle_now_func(), dt)))
#         self.dir(freq)
        angle_now = self.angle_now_func()
        freq = int(round(self.accel(self.angle_now)))
        # print(freq, self.angle_target, angle_now, self.angle_target - angle_now)
        self.dir(self.angle_target - angle_now)

        if self.pwm is not None:
            #self.pwm.init(freq=abs(freq), duty_u16=32768)  # 50%
            self.pwm.freq(abs(freq))
            self.pwm.duty_u16(32768)  # 50%

    def stop_pulses(self):
        try:
            self.pwm.duty_u16(0)
        except:
            pass
        self.dir(0)

    def dir(self, delta):
        # Set rotate direction
        _d = self.direction
        self.direction = delta
        if _d != self.direction:
            self.accel._integral = 0  # сброс интегральной составляющей при смене направления

    # -----------------------------------------------------------------------
    def is_ready(self) -> bool:
        angle_now = self.angle_now_func()
        self.__angle_now = angle_now

        #print('angle_target, angle_now, direction', self.angle_target, self.angle_now, self.direction)

        if self.direction > 0:
            if angle_now >= self.angle_max_limit - self.angle_precision:
                self.stop_pulses()
        elif self.direction < 0:
            if angle_now <= self.angle_min_limit + self.angle_precision:
                self.stop_pulses()

        if self.direction > 0:
            if angle_now >= self.angle_target - self.angle_precision:
                self.stop_pulses()
                #print('if self.direction > 0:')
                self.correct_counter()
                return True
        elif self.direction < 0:
            if angle_now <= self.angle_target + self.angle_precision:
                self.stop_pulses()
                #print('if self.direction < 0:')
                self.correct_counter()
                return True

        if abs(self.angle_target - angle_now) <= self.angle_precision:
            self.stop_pulses()
            self.correct_counter()
            return True

        return False

    # -----------------------------------------------------------------------
    def go(self):
        # Perform one step each time in the main loop to achieve the target position
        if 1:#not self.is_ready():
            angle_delta = self.angle_target - self.angle_now_func()
            #angle_delta = self.angle_target - self.__angle_now
            # print('angle_delta=', angle_delta,  self.freq())
            if angle_delta > self.angle_precision * 2:
                self.start_pulses(angle_delta)
            elif angle_delta < -self.angle_precision * 2:
                self.start_pulses(angle_delta)
            else:
                self.stop_pulses()

    def stop(self):
        self.stop_pulses()
        self.angle_target = self.angle_now_func()
