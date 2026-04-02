from micropython import const
from uctypes import BF_POS, BF_LEN, BFUINT16, BIG_ENDIAN, struct, addressof
from utime import sleep_us
from machine import SPI, Pin

# ----------------------------------------------------------------------
__MSB_mask = const(0x4000)  # for lower 15 bits
__to_angle = 360 / 0x4000

# Таблиця парності для 4-бітних нібблів (0-15)
# 0: парне(0), 1: непарне(1), 2: непарне(1), 3: парне(0) і т.д.
_PARITY_LOOKUP = b'\x00\x01\x01\x00\x01\x00\x00\x01\x01\x00\x00\x01\x00\x01\x01\x00'


#@micropython.viper
@micropython.native
def is_even2(data):
    # Працюємо з 16-бітним значенням (адреса + R/W)
    # XOR між усіма 4-бітними частинами числа
    data &= 0x7FFF
    p = data ^ (data >> 8)
    p = p ^ (p >> 4)
    # Повертаємо 0 якщо парне, 1 якщо непарне (для AS5x47 потрібна EVEN parity)
    return _PARITY_LOOKUP[p & 0x0F]


@micropython.native
def is_even1(data):
    # Calc parity bit
    even = False
    msb_mask = __MSB_mask
    while msb_mask:
        if data & msb_mask:
            even = not even
        msb_mask >>= 1
    return 1 if even else 0


@micropython.native
def is_even(data):
    data &= 0x7FFF
    data ^= data >> 8
    data ^= data >> 4
    data ^= data >> 2
    data ^= data >> 1
    return data & 1


# ----------------------------------------------------------------------
# SPI Command Frame
# Name | Bit Position & Bit Length | Description
Command_Frame_struct = {
    "PARC": 15 << BF_POS | 1 << BF_LEN | BFUINT16,  #      Parity bit (even) calculated on the lower 15 bits of command frame
    "R_W": 14 << BF_POS | 1 << BF_LEN | BFUINT16,  #       0: Write, 1: Read
    "ADDR": 0 << BF_POS | 14 << BF_LEN | BFUINT16,  # 13:0 Address to read or write
    }

WRITE = 0  # constants for "Command_Frame_struct.R_W" field
READ = 1

# SPI Read Data Frame
# Name | Bit Position & Bit Length | Description
Read_Data_Frame_struct = {
    "PARD": 15 << BF_POS | 1 << BF_LEN | BFUINT16,  #      Parity bit (even) for the data frame
    "EF": 14 << BF_POS | 1 << BF_LEN | BFUINT16,  #        0: No command frame error occurred, 1: Error occurred
    "DATA": 0 << BF_POS | 14 << BF_LEN | BFUINT16,  # 13:0 Data
    }

# SPI Write Data Frame
# Name | Bit Position & Bit Length | Description
Write_Data_Frame_struct = {
    "PARD": 15 << BF_POS | 1 << BF_LEN | BFUINT16,  #      Parity bit (even)
    "LOW": 14 << BF_POS | 1 << BF_LEN | BFUINT16,  #       Always low
    "DATA": 0 << BF_POS | 14 << BF_LEN | BFUINT16,  # 13:0 Data
    }

# ----------------------------------------------------------------------
# Volatile Register Table
# Name | Address    | Default | Description
NOP = 0x0000  #       0x0000    No operation
ERRFL = 0x0001  #     0x0000    Error register
PROG = 0x0003  #      0x0000    Programming register
DIAAGC = 0x3FFC  #    0x0180    Diagnostic and AGC
MAG = 0x3FFD  #       0x0000    CORDIC magnitude
ANGLEUNC = 0x3FFE  #  0x0000    Measured angle without dynamic angle error compensation
ANGLECOM = 0x3FFF  #  0x0000    Measured angle with dynamic angle error compensation

# Defining structure layouts for registers:

# ERRFL (0x0001)
# Name | Bit Position & Bit Length | Read/Write | Description
ERRFL_struct = {
    "PARERR": 2 << BF_POS | 1 << BF_LEN | BFUINT16,  #  R Parity error
    "INVCOMM": 1 << BF_POS | 1 << BF_LEN | BFUINT16,  # R Invalid command error: set to 1 by reading or writing an invalid register address
    "FRERR": 0 << BF_POS | 1 << BF_LEN | BFUINT16,  #   R Framing error: is set to 1 when a non-compliant SPI frame is detected
    }

# PROG (0x0003)
# Name | Bit Position & Bit Length | Read/Write | Description
PROG_struct = {
    "PROGVER": 6 << BF_POS | 1 << BF_LEN | BFUINT16,  # R/W Program verify: must be set to 1 for verifying the correctness of the OTP programming
    "PROGOTP": 3 << BF_POS | 1 << BF_LEN | BFUINT16,  # R/W Start OTP programming cycle
    "OTPREF": 2 << BF_POS | 1 << BF_LEN | BFUINT16,  #  R/W Refreshes the non-volatile memory content with the OTP programmed content
    "PROGEN": 0 << BF_POS | 1 << BF_LEN | BFUINT16,  #  R/W Program OTP enable: enables programming the entire OTP memory
    }

# DIAAGC (0x3FFC)
# Name | Bit Position & Bit Length | Read/Write | Description
DIAAGC_struct = {
    "MAGL": 11 << BF_POS | 1 << BF_LEN | BFUINT16,  #   R Diagnostics: Magnetic field strength too low; AGC=0xFF
    "MAGH": 10 << BF_POS | 1 << BF_LEN | BFUINT16,  #   R Diagnostics: Magnetic field strength too high; AGC=0x00
    "COF": 9 << BF_POS | 1 << BF_LEN | BFUINT16,  #     R Diagnostics: CORDIC overflow
    "LF": 8 << BF_POS | 1 << BF_LEN | BFUINT16,  #      R Diagnostics: Offset compensation
    #                                                                  LF=0:internal offset loops not ready regulated
    #                                                                  LF=1:internal offset loop finished
    "AGC": 0 << BF_POS | 8 << BF_LEN | BFUINT16,  # 7:0 R Automatic gain control value
    }

# MAG (0x3FFD)
# Name | Bit Position & Bit Length | Read/Write | Description
MAG_struct = {
    "CMAG": 0 << BF_POS | 14 << BF_LEN | BFUINT16,  # 13:0 R CORDIC magnitude information
    }

# ANGLE (0x3FFE)
# Name | Bit Position & Bit Length | Read/Write | Description
ANGLEUNC_struct = {
    "CORDICANG": 0 << BF_POS | 14 << BF_LEN | BFUINT16,  # 13:0 R Angle information without dynamic angle error compensation
    }

# ANGLECOM (0x3FFF)
# Name | Bit Position & Bit Length | Read/Write | Description
ANGLECOM_struct = {
    "DAECANG": 0 << BF_POS | 14 << BF_LEN | BFUINT16,  # 13:0 R Angle information with dynamic angle error compensation
    }

# ----------------------------------------------------------------------
# Non-Volatile Register Table
# Name | Address       | Default | Description
ZPOSM = 0x0016  #        0x0000    Zero position MSB
ZPOSL = 0x0017  #        0x0000    Zero position LSB /MAG diagnostic
SETTINGS1 = 0x0018  #    0x0001    Custom setting register 1
SETTINGS2 = 0x0019  #    0x0000    Custom setting register 2

# Defining structure layouts for registers:

# ZPOSM (0x0016)
# Name | Bit Position & Bit Length | Read/Write/Program | Description
ZPOSM_struct = {
    "ZPOSM": 0 << BF_POS | 8 << BF_LEN | BFUINT16,  #       7:0 R/W/P 8 most significant bits of the zero position
    }

# ZPOSL (0x0017)
# Name | Bit Position & Bit Length | Read/Write/Program | Description
ZPOSL_struct = {
    "ZPOSL": 0 << BF_POS | 6 << BF_LEN | BFUINT16,  #       5:0 R/W/P 6 least significant bits of the zero position
    "COMP_L_ERROR_EN": 6 << BF_POS | 1 << BF_LEN | BFUINT16,  # R/W/P This bit enables the contribution of MAGH (magnetic field strength too high) to the error flag
    "COMP_H_ERROR_EN": 7 << BF_POS | 1 << BF_LEN | BFUINT16,  # R/W/P This bit enables the contribution of MAGL (magnetic field strength too low) to the error flag
    }

# SETTINGS1 (0x0018)
# Name | Bit Position & Bit Length | Read/Write/Program | Description
SETTINGS1_struct = {
    "FACTORY_SETTING": 0 << BF_POS | 1 << BF_LEN | BFUINT16,  # R     Pre-Programmed to 1
    "NOT_USED": 1 << BF_POS | 1 << BF_LEN | BFUINT16,  #        R/W/P Pre-Programmed to 0, must not be overwritten.
    "DIR": 2 << BF_POS | 1 << BF_LEN | BFUINT16,  #             R/W/P Rotation direction
    "UVW_ABI": 3 << BF_POS | 1 << BF_LEN | BFUINT16,  #         R/W/P Defines the PWM Output
    #                                                                                         (0 = ABI is operating, W is used as PWM, 1 = UVW is operating, I is used as PWM)
    "DAECDIS": 4 << BF_POS | 1 << BF_LEN | BFUINT16,  #         R/W/P Disable Dynamic Angle Error Compensation
    #                                                                                         (0 = DAE compensation ON, 1 = DAE compensation OFF)
    "ABIBIN": 5 << BF_POS | 1 << BF_LEN | BFUINT16,  #          R/W/P ABI decimal or binary selection of the ABI pulses per revolution
    "DATASELECT": 6 << BF_POS | 1 << BF_LEN | BFUINT16,  #      R/W/P This bit defines which data can be read form address 16383dec (3FFFhex).
    #                                                                                         (0->DAECANG, 1->CORDICANG)
    "PWMON": 7 << BF_POS | 1 << BF_LEN | BFUINT16,  #           R/W/P Enables PWM (setting of UVW_ABI Bit necessary)
    }

# SETTINGS2 (0x0019)
# Name | Bit Position & Bit Length | Read/Write/Program | Description
SETTINGS2_struct = {
    "UVWPP": 0 << BF_POS | 3 << BF_LEN | BFUINT16,  #       2:0 R/W/P UVW number of pole pairs
    #                                                       (000 = 1, 001 = 2, 010 = 3, 011 = 4, 100 = 5, 101 = 6, 110 = 7, 111 = 7)
    "HYS": 3 << BF_POS | 2 << BF_LEN | BFUINT16,  #         4:3 R/W/P Hysteresis setting
    "ABIRES": 5 << BF_POS | 3 << BF_LEN | BFUINT16,  #      7:5 R/W/P Resolution of ABI
    }
# ----------------------------------------------------------------------


class AS5x47():
    # SPI Interface(slave) communicates at clock rates up to 10 MHz.
    # The AS5047D SPI uses mode=1 (CPOL=0, CPHA=1) to exchange data.
    #
    # The ESP32 polarity can be 0 or 1, and is the level the idle clock line sits at.
    # The ESP32 phase can be 0 or 1 to sample data on the first or second clock edge respectively.
    #
    # The ESP32 polarity is the idle state of SCK.
    # The ESP32 phase=0 means sample on the first edge of SCK, phase=1 means the second.
    #
    # spi = SPI(HSPI_ID, sck=Pin(HSPI_sck), mosi=Pin(HSPI_mosi), miso=Pin(HSPI_miso), baudrate=10_000_000, polarity=0, phase=1, bits=16, firstbit=SPI.MSB)
    # cs = Pin(esp32_.HSPI_cs1, Pin.OUT, value=1)

    # Константи помилок
    NO_error = 0
    EF_error = 1
    PARD_error = 2
    DATA_error = 3

    def __init__(self, spi, spi_baudrate, cs):
        assert isinstance(spi, SPI)
        assert isinstance(cs, Pin)

        self.spi = spi
        # Розрахунок затримки
        self.tclk_2_us = 1_000_000 // (spi_baudrate * 2)  # tH = tclk / 2 ns # Time between last falling edge of CLK and rising edge of cs
        if self.tclk_2_us == 0:
            self.tclk_2_us = 1
        # self.tclk_2_us += 10
        self.cs = cs  # active is low

        # Буфери
        self._write_command = bytearray(b'\xC0\x00')
        self._received_data = bytearray(b'\x00\x00')
        self.received_frame = struct(addressof(self._received_data), Read_Data_Frame_struct, BIG_ENDIAN)
        self._command_buff = bytearray(b'\x00\x00')
        self.command_frame = struct(addressof(self._command_buff), Command_Frame_struct, BIG_ENDIAN)
        self._data_buff = bytearray(b'\x00\x00')
        self.data_frame = struct(addressof(self._data_buff), Write_Data_Frame_struct, BIG_ENDIAN)

        self.error = self.NO_error
        self._angle14 = 0
        self._angle14_prev = 0
        self._angle_major = 0

        self.init_sensor()

    def init_sensor(self):
        """Асинхронна ініціалізація (замість друку в __init__)"""
        err = self.read_ERRFL()
        diag = self.read_DIAAGC()
        print('AS5x47:ERRFL:', err)
        print('AS5x47:DIAAGC:', diag)

        # Початкове зчитування кута
        self.readAngleCom()
        self.readAngleCom()
        self.readAngleCom()
        self._angle14_prev = self._angle14
        if self._angle14_prev >= 0x2000:
            self._angle14_prev = 0

    # ------------------
    @micropython.native
    def _readAngleInfinity(self, readAngleFunc):
        readAngleFunc()
        if not self.error:
            delta = self._angle14 - self._angle14_prev
            if delta >= 0x2000:
                self._angle_major -= 0x4000
            elif delta <= -0x2000:
                self._angle_major += 0x4000
            self._angle14_prev = self._angle14
        return (self._angle14 + self._angle_major) * __to_angle

    def __repr__(self):
        return 'AS5x47(spi={}, cs={})'.format(self.spi, self.cs)

    def writeData(self, command, value):
        # Send command
        self.cs(0)
        self.spi.write(command)
        sleep_us(self.tclk_2_us)
        self.cs(1)

        # Send data
        self.cs(0)
        self.spi.write(value)
        sleep_us(self.tclk_2_us)
        self.cs(1)

    # after every spi.write_readinto()
    def checkReceivedFrame(self, where=''):
        if self.received_frame.EF:
            print('received_frame.EF on 0x%X' % self.command_frame.ADDR)
            self.error = self.EF_error
            #raise
        #el
        if self.received_frame.PARD != is_even(self.received_frame.DATA):
            print('received_frame.PARD != is_even on 0x%X' % self.command_frame.ADDR)
            print(where, self.EF_error, self.received_frame.PARD, self.received_frame.DATA, self._received_data)
            self.error = self.PARD_error
            #raise
        #el
        if self._received_data == b'\xff\xff':
            print("_received_data == b'\xff\xff'")
            self.error = self.DATA_error
            #raise
        else:
            self.error = self.NO_error
        #print("checkReceivedFrame()", where)

    def readData(self, command):
        # Send Read Command
        self._write_command = command  # bytes_at(addressof(command), sizeof(command))
        self.cs(0)
        self.spi.write(self._write_command)
        sleep_us(self.tclk_2_us)
        self.cs(1)

        # Send Read Command while receiving data
        self.cs(0)
        self.spi.write_readinto(self._write_command, self._received_data)
        sleep_us(self.tclk_2_us)
        self.cs(1)

        self.checkReceivedFrame("readData")

    @micropython.native
    def readDataAgain(self):
        # Send Read Command while receiving data
        self.cs(0)
        self.spi.write_readinto(self._write_command, self._received_data)
        sleep_us(self.tclk_2_us)
        self.cs(1)

        self.checkReceivedFrame("readDataAgain")

    def receivedFrameStruct(self, received_frame):
        return struct(addressof(received_frame), Read_Data_Frame_struct, BIG_ENDIAN)

    @micropython.native
    def readRegister(self, registerAddress):
        self.command_frame.ADDR = registerAddress
        self.command_frame.R_W = READ
        # Розрахунок парності (синхронна операція)
        self.command_frame.PARC = is_even(int.from_bytes(self._command_buff, byteorder="big"))
        self.readData(self.command_frame)

#     def readRegisterAgain(self):
#         self.readDataAgain()

    @micropython.native
    def writeRegister(self, registerAddress, registerValue):
        self.command_frame.ADDR = registerAddress
        self.command_frame.R_W = WRITE
        self.command_frame.PARC = is_even(int.from_bytes(self._command_buff, byteorder="big"))

        self.data_frame.DATA = registerValue
        self.data_frame.LOW = 0
        self.data_frame.PARD = is_even(int.from_bytes(self._data_buff, byteorder="big"))

        self.writeData(self.command_frame, self.data_frame)

#     # ------------------
#
#     def readAngle(self):
#         self.readRegister(ANGLEUNC)
#         if not self.error:
#             self._angle14 = struct(addressof(self._received_data), ANGLEUNC_struct, BIG_ENDIAN).CORDICANG
#
#
#     def readAngleAgain(self):
#         self.readDataAgain()
#         if not self.error:
#             self._angle14 = struct(addressof(self._received_data), ANGLEUNC_struct, BIG_ENDIAN).CORDICANG
#
#
#     def readAngleInfinity(self):
#         return self._readAngleInfinity(self.readAngleAgain)

    # ------------------
    @micropython.native
    def readAngleCom(self):
        self.readRegister(ANGLECOM)
        if not self.error:
            self._angle14 = struct(addressof(self._received_data), ANGLECOM_struct, BIG_ENDIAN).DAECANG
        return self._angle14

    @micropython.native
    def readAngleComAgain(self):
        self.readDataAgain()
        if not self.error:
            self._angle14 = struct(addressof(self._received_data), ANGLECOM_struct, BIG_ENDIAN).DAECANG
        return self._angle14

    @micropython.native
    def readAngleComInfinity(self):
        return self._readAngleInfinity(self.readAngleComAgain)

    # ------------------
#     def writeSettings1(self, value):
#         self.writeRegister(SETTINGS1, value)

#     def writeSettings2(self, value):
#         self.writeRegister(SETTINGS2, value)

#     def writeZeroPosition(self, zposm, zposl):
#         self.writeRegister(ZPOSM, zposm)
#         self.writeRegister(ZPOSL, zposl)

    def read_DIAAGC(self):
        self.readRegister(DIAAGC)
        if not self.error:
            s = struct(addressof(self._received_data), DIAAGC_struct, BIG_ENDIAN)
            return {'MAGL': s.MAGL, 'MAGH': s.MAGH, 'COF': s.COF, 'LF': s.LF, 'AGC': s.AGC}
        return None

    def read_ERRFL(self):
        self.readRegister(ERRFL)
        if not self.error:
            s = struct(addressof(self._received_data), ERRFL_struct, BIG_ENDIAN)
            return {'PARERR': s.PARERR, 'INVCOMM': s.INVCOMM, 'FRERR': s.FRERR}
        return None
