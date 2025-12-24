# sensors.py

from utime import ticks_us, ticks_diff

#from avg_filter import *
import mahony


class Sensors():
    def __init__(self, mrps, imu):
        self.mrps = mrps
        self.imu = imu

        self.offset_roll = 0
        self.offset_pitch = 0
        self.offset_yaw = 0

        self.raw_roll = 0
        self.raw_pitch = 0
        self.raw_yaw = 0

        self._roll = 0  # discrete
        self._pitch = 0  # discrete
        self._yaw = 0  # discrete
        self.temperature = 0

        self.roll_prev = 0
        self.pitch_prev = 0
        self.yaw_prev = 0
        self.temperature_prev = 0
        
        yaw = mrps.readAngleCom()  # required before mrps.angle
        self._yaw = self.read_yaw()

        self._t_us_IMU = ticks_us()  # us !!!
        
    def __repr__(self):
        return f"Sensors(mrps={self.mrps}, imu={self.imu})"

    def info(self):
        return f"Sensors: roll={self.roll:-5.2}, pitch={self.pitch:-5.2}, yaw={self.yaw:-5.2}, temperature={self.temperature:3}"
        #return f"Sensors: roll={round(self.roll, 2):-5}, pitch={round(self.pitch, 2):-5}, yaw={round(self.yaw, 2):-5}, temperature={self.temperature:-4}"

    @property
    def roll(self):
        return self._roll
    
    @property
    def pitch(self):
        return self._pitch

    @property
    def yaw(self):
        return self._yaw
    
    #@micropython.native
    def get_roll(self):  
        return self._roll

    #@micropython.native
    def get_pitch(self):  
        return self._pitch

    #@micropython.native
    def get_yaw(self):
        return self._yaw

    #@micropython.native
    def handle(self):
        #print('Sensors().handle()')
        _t = ticks_us()  # us !!!
        t = self.imu.temperature
        a = self.imu.acceleration
        g = self.imu.gyro
        if not self.imu.error:
#             mahony.MahonyAHRSupdateIMU(
#                -g[1],
#                 g[0],
#                 g[2],  # датчик горизонтально # сова 3 и 4 провода идут влево внутрь ????
#                -a[1],
#                 a[0],
#                 a[2],
#                 ticks_diff(_t, self._t_us_IMU)
#                 )
            mahony.MahonyAHRSupdateIMU(
                -g[1],
                -g[0],
                g[2],  # датчик горизонтально # сова 3 и 4 провода идут влево внутрь
                -a[1],
                -a[0],
                a[2],
                ticks_diff(_t, self._t_us_IMU)
                )
            self._t_us_IMU = _t
            
            self.raw_roll = mahony.Mahony_roll()
            self.raw_pitch = mahony.Mahony_pitch()
            self._roll = round(self.raw_roll + self.offset_roll, 2)  # discrete
            self._pitch = round(self.raw_pitch + self.offset_pitch, 2)  # discrete
            self.temperature = round(t, 1)
            
            self.pitch_prev = self._pitch
            self.roll_prev = self._roll
            self.temperature_prev = self.temperature
        else:
            print("self.imu.error PREV DATA")
            self._pitch = self.pitch_prev
            self._roll = self.roll_prev
            self.temperature = self.temperature_prev

        self.read_yaw() 

    #@micropython.native
    def read_yaw(self):  # instant
        self.raw_yaw = self.mrps.readAngleComInfinity()
        if not self.mrps.error:
            yaw = round(self.raw_yaw + self.offset_yaw, 2)
            self.yaw_prev = yaw
        self._yaw = self.yaw_prev
        return self._yaw
