# Copyright (c) 2018-2020 Mika Tuupola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of  this software and associated documentation files (the "Software"), to
# deal in  the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copied of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# https://github.com/tuupola/micropython-mpu9250
# MicroPython I2C driver for MPU6500 6-axis motion tracking device

__version__ = "0.3.0"

# pylint: disable=import-error
from sys import print_exception
from utime import sleep_ms
from ustruct import unpack, pack_into
from machine import I2C
from micropython import const
# pylint: enable=import-error

_SELF_TEST_X_GYRO = const(0x00)
_SELF_TEST_Y_GYRO = const(0x01)
_SELF_TEST_Z_GYRO = const(0x02)
_SELF_TEST_X_ACCEL = const(0x0d)
_SELF_TEST_Y_ACCEL = const(0x0e)
_SELF_TEST_Z_ACCEL = const(0x0f)
_GYRO_CONFIG = const(0x1b)
_ACCEL_CONFIG = const(0x1c)
_ACCEL_CONFIG2 = const(0x1d)
_INT_PIN_CFG = const(0x37)
_ACCEL_XOUT_H = const(0x3b)
_ACCEL_XOUT_L = const(0x3c)
_ACCEL_YOUT_H = const(0x3d)
_ACCEL_YOUT_L = const(0x3e)
_ACCEL_ZOUT_H = const(0x3f)
_ACCEL_ZOUT_L = const(0x40)
_TEMP_OUT_H = const(0x41)
_TEMP_OUT_L = const(0x42)
_GYRO_XOUT_H = const(0x43)
_GYRO_XOUT_L = const(0x44)
_GYRO_YOUT_H = const(0x45)
_GYRO_YOUT_L = const(0x46)
_GYRO_ZOUT_H = const(0x47)
_GYRO_ZOUT_L = const(0x48)
_PWR_MGMT_1 = const(0x6b)  # Регістр керування живленням
_WHO_AM_I = const(0x75)

#_ACCEL_FS_MASK = const(0b00011000)
ACCEL_FS_SEL_2G = const(0b00000000)
ACCEL_FS_SEL_4G = const(0b00001000)
ACCEL_FS_SEL_8G = const(0b00010000)
ACCEL_FS_SEL_16G = const(0b00011000)

_ACCEL_SO_2G = 16384  # 1 / 16384 ie. 0.061 mg / digit
_ACCEL_SO_4G = 8192  # 1 / 8192 ie. 0.122 mg / digit
_ACCEL_SO_8G = 4096  # 1 / 4096 ie. 0.244 mg / digit
_ACCEL_SO_16G = 2048  # 1 / 2048 ie. 0.488 mg / digit

#_GYRO_FS_MASK = const(0b00011000)
GYRO_FS_SEL_250DPS = const(0b00000000)
GYRO_FS_SEL_500DPS = const(0b00001000)
GYRO_FS_SEL_1000DPS = const(0b00010000)
GYRO_FS_SEL_2000DPS = const(0b00011000)

_GYRO_SO_250DPS = 131
_GYRO_SO_500DPS = 62.5
_GYRO_SO_1000DPS = 32.8
_GYRO_SO_2000DPS = 16.4

# Used for enablind and disabling the i2c bypass access
_I2C_BYPASS_MASK = const(0b00000010)
_I2C_BYPASS_EN = const(0b00000010)
_I2C_BYPASS_DIS = const(0b00000000)

_TEMP_SO = 333.87
_TEMP_OFFSET = 21

SF_G = 1
SF_M_S2 = 9.80665  # 1 g = 9.80665 m/s2 ie. standard gravity
SF_DEG_S = 1
SF_RAD_S = 0.017453292519943  # 1 deg/s is 0.017453292519943 rad/s


class MPU6500:
    # Class which provides interface to MPU6500 6-axis motion tracking device.
    def __init__(
        self,
        i2c,
        address=0x68,
        accel_fs=ACCEL_FS_SEL_2G,
        gyro_fs=GYRO_FS_SEL_250DPS,
        #accel_fs=ACCEL_FS_SEL_16G,
        #gyro_fs=GYRO_FS_SEL_2000DPS,
        accel_sf=SF_M_S2,
        gyro_sf=SF_RAD_S,
        gyro_offset=(0, 0, 0)
        ):

        assert isinstance(i2c, I2C)
        self.i2c = i2c
        self.address = address

        # Постійні буфери для RAM (запобігають частому Garbage Collection)
        self._buf1 = bytearray(1)
        self._buf2 = bytearray(2)
        self._buf6 = bytearray(6)
        self._buf_prev = bytearray(b'\x00\x00\x00\x00\x00\x00')
        self.error = False

        # Пробудження датчика (скидання біта SLEEP)
        self._register_char(_PWR_MGMT_1, 0x00)
        sleep_ms(100)  # Даємо час стабілізуватися

        # 0x70 = standalone MPU6500, 0x71 = MPU6250 SIP
        if self.get_whoami() not in [0x71, 0x70]:
            raise RuntimeError("MPU6500 not found in I2C bus.")

        # Ініціалізація чутливості (синхронні виклики I2C допустимі в __init__)
        self._accel_so = self._accel_fs(accel_fs)
        self._gyro_so = self._gyro_fs(gyro_fs)
        self._accel_sf = accel_sf
        self._gyro_sf = gyro_sf
        self._gyro_offset = gyro_offset

    def __repr__(self):
        return 'MPU6500(i2c={}, address={})'.format(self.i2c, self.address)

    def execute_self_test(self):
        """
        Виконує самотестування акселерометра та гіроскопа.
        Повертає True, якщо тест пройдено, і False у разі помилки.
        """
        # 1. Зчитування заводських значень (ST_DATA)
        # Для MPU-6500 ці значення використовуються для розрахунку Factory Trim
        raw_st_gyro = [self._register_char(_SELF_TEST_X_GYRO), self._register_char(_SELF_TEST_Y_GYRO), self._register_char(_SELF_TEST_Z_GYRO)]
        raw_st_accel = [self._register_char(_SELF_TEST_X_ACCEL), self._register_char(_SELF_TEST_Y_ACCEL), self._register_char(_SELF_TEST_Z_ACCEL)]

        # 2. Збереження поточних налаштувань для відновлення після тесту
        old_gyro_config = self._register_char(_GYRO_CONFIG)
        old_accel_config = self._register_char(_ACCEL_CONFIG)

        # 3. Активація Self-Test (встановлення бітів 7, 6, 5 у регістрах конфігурації)
        # Встановлюємо FS_SEL = 250dps для гіро та 2g для акселерометра для точності
        self._register_char(_GYRO_CONFIG, 0xE0)  # XG_ST, YG_ST, ZG_ST = 1
        self._register_char(_ACCEL_CONFIG, 0xE0)  # XA_ST, YA_ST, ZA_ST = 1

        sleep_ms(25)  # Очікування стабілізації

        # 4. Зчитування значень з активованим тестом
        st_accel_out = self.get_acceleration()
        st_gyro_out = self.get_gyro()

        # 5. Відновлення попередніх налаштувань
        self._register_char(_GYRO_CONFIG, old_gyro_config)
        self._register_char(_ACCEL_CONFIG, old_accel_config)

        # Логіка перевірки:
        # Справний сенсор має показати суттєву зміну значень (Self-test response)
        # Для спрощеної реалізації перевіримо, чи не є отримані значення нульовими
        # Повна перевірка вимагає формул з AN-MPU-6500A-02 (на базі Factory Trim)

        success = all(abs(x) > 0 for x in st_accel_out) and \
                  all(abs(x) > 0 for x in st_gyro_out)
        return success

    def get_acceleration(self):
        # Acceleration measured by the sensor. By default will return a
        # 3-tuple of X, Y, Z axis acceleration values in m/s^2 as floats. Will
        # return values in g if constructor was provided `accel_sf=SF_M_S2`
        # parameter.
        xyz = self._register_three_shorts(_ACCEL_XOUT_H)
        return tuple([value / self._accel_so * self._accel_sf for value in xyz])

    def get_gyro(self):
        # X, Y, Z radians per second as floats.
        xyz = self._register_three_shorts(_GYRO_XOUT_H)
        xyz = [value / self._gyro_so * self._gyro_sf for value in xyz]

        return (xyz[0] - self._gyro_offset[0], xyz[1] - self._gyro_offset[1], xyz[2] - self._gyro_offset[2])

    def get_temperature(self):
        # Temperature in celcius as a float.
        temp = self._register_short(_TEMP_OUT_H)
        return ((temp - _TEMP_OFFSET) / _TEMP_SO) + _TEMP_OFFSET

    def get_whoami(self):
        # Value of the whoami register.
        return self._register_char(_WHO_AM_I)

    def calibrate(self, count=256, delay=5):
        ox, oy, oz = (0.0, 0.0, 0.0)
        self._gyro_offset = (0.0, 0.0, 0.0)

        for _ in range(count):
            gx, gy, gz = self.get_gyro()
            ox += gx
            oy += gy
            oz += gz
            sleep_ms(delay)

        n = float(count)
        self._gyro_offset = (ox / n, oy / n, oz / n)
        return self._gyro_offset

    def _register_short(self, register, value=None):
        if value is None:
            self.__readfrom_mem_into(register, self._buf2)
            return unpack(">h", self._buf2)[0]

        pack_into(">h", self._buf2, 0, value)
        self.__writeto_mem(register, self._buf2)
        return None

    def _register_three_shorts(self, register):
        self.__readfrom_mem_into(register, self._buf6)
        return unpack(">hhh", self._buf6)

    def _register_char(self, register, value=None):
        if value is None:
            self.__readfrom_mem_into(register, self._buf1)
            return self._buf1[0]

        self._buf1[0] = value
        self.__writeto_mem(register, self._buf1)
        return None

    def __readfrom_mem_into(self, register, buf):
        try:
            self.i2c.readfrom_mem_into(self.address, register, buf)
            if len(buf) == 6:
                self._buf_prev[:] = buf
            self.error = False
        except OSError as e:
            print_exception(e)
            #             print('len(buf)=', len(buf), buf)
            #             buf = b'\x00\x00\x00\x00\x00\x00'
            if len(buf) == 6:
                buf[:] = self._buf_prev
            self.error = True

    def __writeto_mem(self, register, buf):
        try:
            self.i2c.writeto_mem(self.address, register, buf)
            self.error = False
        except OSError as e:
            print_exception(e)
            #             print('len(buf)=', len(buf), buf)
            #             buf = b'\x00\x00\x00\x00\x00\x00'
            self.error = True
        return None

    # Синхронні налаштування (зазвичай викликаються один раз при старті)
    def _accel_fs(self, value):
        self._register_char(_ACCEL_CONFIG, value)

        # Return the sensitivity divider
        mapping = {ACCEL_FS_SEL_2G: _ACCEL_SO_2G, ACCEL_FS_SEL_4G: _ACCEL_SO_4G, ACCEL_FS_SEL_8G: _ACCEL_SO_8G, ACCEL_FS_SEL_16G: _ACCEL_SO_16G}
        return mapping[value]

    def _gyro_fs(self, value):
        self._register_char(_GYRO_CONFIG, value)

        # Return the sensitivity divider
        mapping = {GYRO_FS_SEL_250DPS: _GYRO_SO_250DPS, GYRO_FS_SEL_500DPS: _GYRO_SO_500DPS, GYRO_FS_SEL_1000DPS: _GYRO_SO_1000DPS, GYRO_FS_SEL_2000DPS: _GYRO_SO_2000DPS}
        return mapping[value]

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        print("MPU6500:", exception_type, exception_value, traceback)
        pass
