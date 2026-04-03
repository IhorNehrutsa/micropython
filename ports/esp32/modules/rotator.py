# rotator.py

from sys import print_exception
from micropython import schedule
from utime import ticks_ms, ticks_diff, sleep_ms
from machine import Timer
import power
from mks_servo_can.mks_enums import *

print(MotorStatus())

BREAK_ANGLE = 270


class Rotator():
    def __init__(self, azim, elev, sensors, rotator_period=100, motor_period=0):  # rotator_period in ms
        self.azim = azim
        self.elev = elev
        self.sensors = sensors

        self.rotator_period = rotator_period
        self.motor_period = motor_period

        self.t_handle_motors = 0  # час попереднього запуску

        self.dt_handle_sensors = 0
        self.dt_handle_motors = 0

        self.timer = None

    def __repr__(self):
        return f"Rotator(azim={self.azim}, elev={self.elev}, sensors={self.sensors}, rotator_period={self.rotator_period}, motor_period={self.motor_period})"

    def info(self):
        return f"Rotator: targets={self.azim.angle_target}, {self.elev.angle_target}, dt={self.dt_handle_sensors}, {self.dt_handle_motors}, {self.sensors.info()}, {self.azim.info()}, {self.elev.info()}"

    def deinit(self):
        try:
            self.timer_deinit()
        except:
            pass
        try:
            self.azim.deinit()
        except:
            pass
        try:
            self.elev.deinit()
        except:
            pass

    def start_timer(self):
        if self.timer is None:
            #self.timer = Timer(-2, mode=Timer.PERIODIC, period=self.rotator_period, callback=self.__timer_callback)
            self.timer = Timer(3, mode=Timer.PERIODIC, period=self.rotator_period, callback=self.__timer_callback)

    def timer_deinit(self):
        if self.timer is not None:
            try:
                self.timer.deinit()
                print('Rotator.timer.deinit()')
            except:
                pass
            self.timer = None

    @micropython.native
    def handle_sensors(self):
        t = ticks_ms()

        self.sensors.handle()

        t = ticks_diff(ticks_ms(), t)
        if t > 0:
            self.dt_handle_sensors = t

    @micropython.native
    def handle_motors(self):
        t = ticks_ms()

        if ticks_diff(t, self.t_handle_motors) >= self.motor_period:
            self.t_handle_motors = t

            if power.seconds_after_power_off > 0:
                if self.azim.parking_position is not None:
                    self.azim.angle_target = self.azim.parking_position
                if self.elev.parking_position is not None:
                    self.elev.angle_target = self.elev.parking_position

            if abs(self.azim.angle_counter - self.azim.angle_now) > BREAK_ANGLE:
                self.azim.stop_pulses()
            else:
                self.azim.go()

            sleep_ms(300)

            if abs(self.elev.angle_counter - self.elev.angle_now) > BREAK_ANGLE:
                self.elev.stop_pulses()
            else:
                self.elev.go()

            tmp = ticks_diff(ticks_ms(), t)
            if tmp > 0:
                self.dt_handle_motors = tmp

    # --- Метод, що виконується в основному циклі (Has GIL) ---
    #@micropython.native
    def _timer_callback(self, timer):
        try:
            self.handle_sensors()
            
            self.handle_motors()
                
            sleep_ms(1)
            
        except KeyboardInterrupt as e:
            print_exception(e)
            self.timer_deinit()
            raise e

    # --- Метод, що виконується в контексті переривання (ISR/No GIL) ---
    #@micropython.native
    def __timer_callback(self, timer):
        try:
            schedule(self._timer_callback, timer)
            sleep_ms(1)
        except BaseException as e:
            print_exception(e)
            raise e

    def go(self):
        self.azim.go()
        self.elev.go()

    @property
    def ready(self):
        return self.azim.is_ready(), self.elev.is_ready()

    #@micropython.native
    def is_ready(self):
        return self.azim.is_ready() and self.elev.is_ready()

    def wait(self, prn=False):
        if prn: print('r.targets', self.targets)
        if prn: print('r.angles', self.angles, end='\r')
        t = ticks_ms()
        while not self.is_ready():
            if prn and ticks_diff(ticks_ms(), t) > 300:
                t = ticks_ms()
                print(f'Angles: {self.angles}', end='                                                        \r')
                #print('r.angles', r.angles, r.elev.info(), r.elev.angle_counter, end='                                                        \r')
                #print('r.angles', r.angles, r.azim.angle_counter, r.elev.angle_counter, end='                                                        \r')
            sleep_ms(10)
        if prn: print('r.angles', self.angles, '                                                        ')
        if prn: print('!READY!')

    @property
    #@micropython.native
    def angles(self):
        return self.azim.angle_now, self.elev.angle_now

    @property
    #@micropython.native
    def angle_counters(self):
        return self.azim.angle_counter, self.elev.angle_counter

    @property
    #@micropython.native
    def targets(self):
        return self.azim.angle_target, self.elev.angle_target

    @targets.setter
    #@micropython.native
    def targets(self, angles):
        self.azim.angle_target, self.elev.angle_target = angles
        self.handle_motors()

    @property
    def rpm(self):
        return self.azim.rpm, self.elev.rpm

    @property
    def rpm_high(self):
        return self.azim.rpm_high, self.elev.rpm_high

    @rpm_high.setter
    def rpm_high(self, rpm):
        self.azim.rpm_high, self.elev.rpm_high = rpm

    @property
    def rps_high(self):
        return self.azim.rps_high, self.elev.rps_high

    @rps_high.setter
    def rps_high(self, rps):
        self.azim.rps_high, self.elev.rps_high = rps

    @property
    def rpm_low(self):
        return self.azim.rpm_low, self.elev.rpm_low

    @rpm_low.setter
    def rpm_low(self, rpm):
        self.azim.rpm_low, self.elev.rpm_low = rpm

    @property
    def rps_low(self):
        return self.azim.rps_low, self.elev.rps_low

    @rps_low.setter
    def rps_low(self, rps):
        self.azim.rps_low, self.elev.rps_low = rps

    @property
    #@micropython.native
    def raw_angles(self):
        return self.sensors.raw_yaw, self.sensors.raw_pitch
