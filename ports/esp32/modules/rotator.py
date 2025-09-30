# rotator.py

from time import ticks_ms, ticks_diff, sleep_ms
from machine import Timer
from _thread import start_new_thread
import power

BREAK_ANGLE = 360 * 2 


class Rotator():
    def __init__(self, azim, elev, sensors, rotator_period=100):  # rotator_period in ms
        self.azim = azim
        self.elev = elev
        self.sensors = sensors

        self.dt_handle_sensors = 0
        self.dt_handle_motors = 0

        self.t_handle_motors = 0
        self.rotator_period_real = 0

        self.rotator_period = rotator_period

        self.is_handle_motors = False

        self.timer = None

        self.is_thread = 0
        self.thread_ms = ticks_ms()

    def __repr__(self):
        return f"Rotator(azim={self.azim}, elev={self.elev}, sensors={self.sensors}, rotator_period={self.rotator_period})"

    def prn(self):
        #print('yaw:{:5.1f} pitch:{:5.1f} slef.azim.angle:{:5.1f} elev.angle:{:5.1f}'.format(self.sensors.yaw, self.sensors.pitch, self.azim.angle, self.elev.angle), self.azim.freq(), self.elev.freq() )#, end=' \r')
        print('yaw', self.sensors.yaw, 'pitch', self.sensors.pitch, 'targets', self.azim.angle_target, self.elev.angle_target, 'freqs', self.azim.freq(), self.elev.freq(), 'dt', self.dt_handle_sensors, self.dt_handle_motors)  #, end=' \r')

    def deinit(self):
        try:
            self.deinit_timer()
        except:
            pass
        try:
            self.stop_thread()
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
        if self.is_thread <= 0:
            if self.timer is None:
                self.timer = Timer(-2, mode=Timer.PERIODIC, period=self.rotator_period, callback=self.__handle_motors)
                # self.timer = Timer(-2, mode=Timer.ONE_SHOT, period=self.rotator_period, callback=self.__timer_motors)

    def deinit_timer(self):
        if self.timer is not None:
            try:
                self.timer.deinit()
                print('rotator.py: timer.deinit()')
            except Exception as e:
                pass
        self.timer = None

    #@micropython.native
    def handle_sensors(self):
        t = ticks_ms()

        self.sensors.handle()

        tmp = ticks_diff(ticks_ms(), t)
        if tmp > 0:
            self.dt_handle_sensors = tmp

    #@micropython.native
    def handle_motors(self):
        # print('handle_motors()')
        try:
            t = ticks_ms()

            self.rotator_period_real = ticks_diff(t, self.t_handle_motors)
            self.t_handle_motors = t

#             if self.is_handle_motors:
#                 print('handle_motors() too long !!! self.rotator_period_real=', self.rotator_period_real)
#                 return
            while not self.is_handle_motors:
                self.is_handle_motors = True

    #        t = ticks_ms()

            self.handle_sensors()

            if power.seconds_after_power_off > 0:
                if self.azim.parking_position is not None:
                    self.azim.angle_target = self.azim.parking_position
                if self.elev.parking_position is not None:
                    self.elev.angle_target = self.elev.parking_position

            if abs(self.azim.angle_counter - self.azim.angle_now) > BREAK_ANGLE:
                #print(f'self.azim: {self.azim.direction} {self.azim.angle_counter} - {self.azim.angle_now} > {BREAK_ANGLE}°', self.azim.info())
                self.azim.stop_pulses()
                # self.azim.set_dir(-self.azim.direction)
            else:
                self.azim.go()

            if abs(self.elev.angle_counter - self.elev.angle_now) > BREAK_ANGLE:
                #print(f'self.elev: {self.elev.direction} {self.elev.angle_counter} - {self.elev.angle_now} > {BREAK_ANGLE}°', self.elev.info())
                self.elev.stop_pulses()
                # self.elev.set_dir(-self.elev.direction)
            else:
                self.elev.go()

    #         tmp = ticks_diff(ticks_ms(), t)
    #         if tmp > 0:
    #             self.dt_handle_motors = tmp

            while self.is_handle_motors:
                self.is_handle_motors = False

            tmp = ticks_diff(ticks_ms(), t)
            if tmp > 0:
                self.dt_handle_motors = tmp
        except KeyboardInterrupt as e:
            print(e, 'handle_motors()')
            raise e

    #@micropython.native
    def __handle_motors(self, timer):
        try:
            self.handle_motors()
        except KeyboardInterrupt as e:
            print(e, 'handle_motors()')
            raise e

#     #@micropython.native
#     def __timer_motors(self, timer):
#         self.handle_motors()
#         if self.rotator_period > self.dt_handle_motors:
#             t = self.rotator_period - self.dt_handle_motors
#         else:
#             t = self.rotator_period
#         self.timer.init(mode=Timer.ONE_SHOT, period=t, callback=self.__timer_motors)

    #@micropython.native
    def __thread_motors(self):
        while self.is_thread > 0:
            if ticks_diff(t := ticks_ms(), self.thread_ms) >= self.rotator_period:
                self.thread_ms = t
                self.handle_motors()
            sleep_ms(10)
        self.is_thread = -1
        #print('self.is_thread', self.is_thread)

    def start_thread(self):
        if self.timer is None:
            if self.is_thread <= 0:
                self.is_thread = 1
                #print('self.is_thread', self.is_thread)
                start_new_thread(self.__thread_motors, ())

    def stop_thread(self):
        if self.is_thread > 0:
            self.is_thread = 0
            #print('self.is_thread', self.is_thread)
            while self.is_thread == 0:
                sleep_ms(20)
            print('stop_thread(), self.is_thread', self.is_thread)

    @property
    def ready(self):
        return self.azim.is_ready(), self.elev.is_ready()

    #@micropython.native
    def is_ready(self):
        return self.azim.is_ready() and self.elev.is_ready()

    def wait(self, prn=False):
        prn and print('r.targets', self.targets)
        prn and print('r.angles', self.angles, end='\r')
        t = ticks_ms()
        while not self.is_ready():
            if ticks_diff(ticks_ms(), t) > 300:
                t = ticks_ms()
                prn and print('r.angles', self.angles, end='                                                        \r')
                #print('r.angles', r.angles, r.elev.info(), r.elev.angle_counter, end='                                                        \r')
                #print('r.angles', r.angles, r.azim.angle_counter, r.elev.angle_counter, end='                                                        \r')
            sleep_ms(10)
        prn and print('r.angles', self.angles, '                                                        ')
        prn and print('!READY!')

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
