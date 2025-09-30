# sensors.py

from utime import ticks_us, ticks_diff

import mahony


class Sensors():
    def __init__(self, mrps, imu):
        self.mrps = mrps
        self.imu = imu

        self.offset_roll = 0
        self.offset_pitch = 0
        self.offset_yaw = 0

        self._roll = 0  # None  # discrete
        self._pitch = 0  # None  # discrete
        self._temperature = 0
        self._yaw = 0  # None  # discrete

        mrps.readAngleCom()  # required before mrps.angle
        self.read_yaw()

        self._t_us_IMU = ticks_us()  # us !!!
        
    @micropython.native
    def __repr__(self):
        return "Sensors(mrps={}, imu={})".format(self.mrps, self.imu)

    @micropython.native
    def info(self):
        return f"Sensors: roll={self._roll:5.1f}, pitch={self._pitch:5.1f}, yaw={self._yaw:5.1f}, temperature={self.temperature:5.1f}"

    @micropython.native
    def handle(self):
        #print('Sensors().handle()')
        _t_us = ticks_us()  # us !!!
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
                ticks_diff(_t_us, self._t_us_IMU)
                )
            self._t_us_IMU = _t_us

            self._pitch = mahony.Mahony_pitch() - self.offset_pitch  # discrete
            self._roll = mahony.Mahony_roll() - self.offset_roll  # discrete
            
        self.read_yaw()


    @micropython.native
    def read_yaw(self):  # instant
        yaw = self.mrps.readAngleComInfinity()
        if not self.mrps.error:
            self._yaw = yaw - self.offset_yaw
        return self._yaw
    
    @micropython.native
    def get_pitch(self):  # discrete
        return round(self._pitch, 2)

    @micropython.native
    def get_roll(self):  # discrete
        return round(self._roll, 2)

    @micropython.native
    def get_yaw(self):  # discrete
        return round(self._yaw, 2)

    @micropython.native
    @property
    def pitch(self):  # discrete
        return round(self._pitch, 2)

    @micropython.native
    @property
    def roll(self):  # discrete
        return round(self._roll, 2)

    @micropython.native
    @property
    def yaw(self):  # discrete
        return round(self._yaw, 2)

    @micropython.native
    @property
    def temperature(self):
        t = self.imu.temperature
        if not self.imu.error:
            self._temperature = round(t, 1)
        return self._temperature
