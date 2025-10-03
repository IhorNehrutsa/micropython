# sensors.py

from utime import ticks_us, ticks_diff

from avg_filter import *
import mahony


class Sensors():
    def __init__(self, mrps, imu):
        self.imu = imu

        self.offset_roll = 0
        self.offset_pitch = 0
        self.offset_yaw = 0

        self.roll = 0  # None  # discrete
        self.pitch = 0  # None  # discrete
        self.temperature = 0  # None

        self.mrps = mrps
        self.yaw = mrps.readAngleCom()  # required before mrps.angle
        self.yaw = self.read_yaw()

        self._t_us_IMU = ticks_us()  # us !!!
        
        self.pitch_prev = 0
        self.roll_prev = 0
        self.temperature_prev = 0
        self.yaw_prev = 0
        
    def __repr__(self):
        return "Sensors(mrps={}, imu={})".format(self.mrps, self.imu)

    def info(self):
        return f"Sensors: roll={self.roll:-5.2}, pitch={self.pitch:-5.2}, yaw={self.yaw:-5.2}, temperature={self.temperature:3}"

    #@micropython.native
    def handle(self):
        #print('Sensors().handle()')
        _t = ticks_us()  # us !!!
        t = self.imu.temperature
        a = self.imu.acceleration
        g = self.imu.gyro
        if not self.imu.error:
            mahony.MahonyAHRSupdateIMU(
               -g[1],
                g[0],
                g[2],  # датчик горизонтально # сова3 провода идут влево внутрь
               -a[1],
                a[0],
                a[2],
                ticks_diff(_t, self._t_us_IMU)
                )
            self._t_us_IMU = _t
            
            self.pitch = round(mahony.Mahony_pitch() - self.offset_pitch, 2)  # discrete
            self.roll = round(mahony.Mahony_roll() - self.offset_roll, 2)  # discrete
            self.temperature = round(t, 1)
            
            self.pitch_prev = self.pitch
            self.roll_prev = self.roll
            self.temperature_prev = self.temperature
        else:
            self.pitch = self.pitch_prev
            self.roll = self.roll_prev
            self.temperature = self.temperature_prev

        yaw = self.read_yaw()  # discrete
        if not self.mrps.error:
            self.yaw = yaw
            self.yaw_prev = yaw
        else:
            self.yaw = self.yaw_prev

    #@micropython.native
    def read_yaw(self):  # instant
        return round(self.mrps.readAngleComInfinity() - self.offset_yaw, 2)
    
    #@micropython.native
    def get_pitch(self):  # discrete
        return self.pitch

    #@micropython.native
    def get_roll(self):  # discrete
        return self.roll

    #@micropython.native
    def get_yaw(self):  # discrete
        return self.yaw
