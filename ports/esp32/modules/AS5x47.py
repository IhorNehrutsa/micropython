from esp32_ import *
from machine import Pin, SPI
import utime as time
import uctypes

# ----------------------------------------------------------------------
MSB_mask = 0x4000  # for lower 15 bits


def isEven(data, MSB_mask):
    # Calc parity bit
    count = 0
    while MSB_mask:
        if data & MSB_mask:
            count += 1
        MSB_mask >>= 1
    return count & 1


# ----------------------------------------------------------------------
# SPI Command Frame
# Name | Bit Position & Bit Length | Description
Command_Frame_struct = {
    "PARC": 15 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #      Parity bit (even) calculated on the lower 15 bits of command frame
    "R_W": 14 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #       0: Write, 1: Read
    "ADDR": 0 << uctypes.BF_POS | 14 << uctypes.BF_LEN | uctypes.BFUINT16,  # 13:0 Address to read or write
    }

WRITE = 0  # constants for "Command_Frame_struct.R_W" field
READ = 1

# SPI Read Data Frame
# Name | Bit Position & Bit Length | Description
Read_Data_Frame_struct = {
    "PARD": 15 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #      Parity bit (even) for the data frame
    "EF": 14 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #        0: No command frame error occurred
    #                                                                              1: Error occurred
    "DATA": 0 << uctypes.BF_POS | 14 << uctypes.BF_LEN | uctypes.BFUINT16,  # 13:0 Data
    }

# SPI Write Data Frame
# Name | Bit Position & Bit Length | Description
Write_Data_Frame_struct = {
    "PARD": 15 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #       Parity bit (even)
    "LOW": 14 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #        Always low
    "DATA": 0 << uctypes.BF_POS | 14 << uctypes.BF_LEN | uctypes.BFUINT16,  # 13:0  Data
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
    "PARERR": 2 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #  R Parity error
    "INVCOMM": 1 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  # R Invalid command error: set to 1 by reading or writing an invalid register address
    "FRERR": 0 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #   R Framing error: is set to 1 when a non-compliant SPI frame is detected
    }

# PROG (0x0003)
# Name | Bit Position & Bit Length | Read/Write | Description
PROG_struct = {
    "PROGVER": 6 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  # R/W Program verify: must be set to 1 for verifying the correctness of the OTP programming
    "PROGOTP": 3 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  # R/W Start OTP programming cycle
    "OTPREF": 2 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #  R/W Refreshes the non-volatile memory content with the OTP programmed content
    "PROGEN": 0 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #  R/W Program OTP enable: enables programming the entire OTP memory
    }

# DIAAGC (0x3FFC)
# Name | Bit Position & Bit Length | Read/Write | Description
DIAAGC_struct = {
    "MAGL": 11 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #   R Diagnostics: Magnetic field strength too low; AGC=0xFF
    "MAGH": 10 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #   R Diagnostics: Magnetic field strength too high; AGC=0x00
    "COF": 9 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #     R Diagnostics: CORDIC overflow
    "LF": 8 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #      R Diagnostics: Offset compensation
    #                                                                             LF=0:internal offset loops not ready regulated
    #                                                                             LF=1:internal offset loop finished
    "AGC": 0 << uctypes.BF_POS | 8 << uctypes.BF_LEN | uctypes.BFUINT16,  # 7:0 R Automatic gain control value
    }

# MAG (0x3FFD)
# Name | Bit Position & Bit Length | Read/Write | Description
MAG_struct = {
    "CMAG": 0 << uctypes.BF_POS | 14 << uctypes.BF_LEN | uctypes.BFUINT16,  #      13:0 R CORDIC magnitude information
    }

# ANGLE (0x3FFE)
# Name | Bit Position & Bit Length | Read/Write | Description
ANGLEUNC_struct = {
    "CORDICANG": 0 << uctypes.BF_POS | 14 << uctypes.BF_LEN | uctypes.BFUINT16,  # 13:0 R Angle information without dynamic angle error compensation
    }

# ANGLECOM (0x3FFF)
# Name | Bit Position & Bit Length | Read/Write | Description
ANGLECOM_struct = {
    "DAECANG": 0 << uctypes.BF_POS | 14 << uctypes.BF_LEN | uctypes.BFUINT16,  #   13:0 R Angle information with dynamic angle error compensation
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
    "ZPOSM": 0 << uctypes.BF_POS | 8 << uctypes.BF_LEN | uctypes.BFUINT16,  #       7:0 R/W/P 8 most significant bits of the zero position
    }

# ZPOSL (0x0017)
# Name | Bit Position & Bit Length | Read/Write/Program | Description
ZPOSL_struct = {
    "ZPOSL": 5 << uctypes.BF_POS | 6 << uctypes.BF_LEN | uctypes.BFUINT16,  #       5:0 R/W/P 6 least significant bits of the zero position
    "COMP_L_ERROR_EN": 6 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  # R/W/P This bit enables the contribution of MAGH (magnetic field strength too high) to the error flag
    "COMP_H_ERROR_EN": 7 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  # R/W/P This bit enables the contribution of MAGL (magnetic field strength too low) to the error flag
    }

# SETTINGS1 (0x0018)
# Name | Bit Position & Bit Length | Read/Write/Program | Description
SETTINGS1_struct = {
    "FACTORY_SETTING": 0 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  # R     Pre-Programmed to 1
    "NOT_USED": 1 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #        R/W/P Pre-Programmed to 0, must not be overwritten.
    "DIR": 2 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #             R/W/P Rotation direction
    "UVW_ABI": 3 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #         R/W/P Defines the PWM Output
    #                                                                                         (0 = ABI is operating, W is used as PWM, 1 = UVW is operating, I is used as PWM)
    "DAECDIS": 4 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #         R/W/P Disable Dynamic Angle Error Compensation
    #                                                                                         (0 = DAE compensation ON, 1 = DAE compensation OFF)
    "ABIBIN": 5 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #          R/W/P ABI decimal or binary selection of the ABI pulses per revolution
    "DATASELECT": 6 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #      R/W/P This bit defines which data can be read form address 16383dec (3FFFhex).
    #                                                                                         (0->DAECANG, 1->CORDICANG)
    "PWMON": 7 << uctypes.BF_POS | 1 << uctypes.BF_LEN | uctypes.BFUINT16,  #           R/W/P Enables PWM (setting of UVW_ABI Bit necessary)
    }

# SETTINGS2 (0x0019)
# Name | Bit Position & Bit Length | Read/Write/Program | Description
SETTINGS2_struct = {
    "UVWPP": 0 << uctypes.BF_POS | 3 << uctypes.BF_LEN | uctypes.BFUINT16,  #       2:0 R/W/P UVW number of pole pairs
    #                                                                                         (000 = 1, 001 = 2, 010 = 3, 011 = 4, 100 = 5, 101 = 6, 110 = 7, 111 = 7)
    "HYS": 3 << uctypes.BF_POS | 2 << uctypes.BF_LEN | uctypes.BFUINT16,  #         4:3 R/W/P Hysteresis setting
    "ABIRES": 5 << uctypes.BF_POS | 3 << uctypes.BF_LEN | uctypes.BFUINT16,  #      7:5 R/W/P Resolution of ABI
    }
# ----------------------------------------------------------------------


class AS5x47():
    # The AS5047D SPI uses mode=1 (CPOL=0, CPHA=1) to exchange data.
    #
    # The ESP32 polarity can be 0 or 1, and is the level the idle clock line sits at.
    # The ESP32 phase can be 0 or 1 to sample data on the first or second clock edge respectively.
    #
    # The ESP32 polarity is the idle state of SCK.
    # The ESP32 phase=0 means sample on the first edge of SCK, phase=1 means the second.
    def __init__(self, _CSn=HSPI_cs0, _SPI_ID=HSPI_ID, _sck=HSPI_sck, _mosi=HSPI_mosi, _miso=HSPI_miso, _baudrate=10000000, _polarity=0, _phase=1, _bits=16, _firstbit=SPI.MSB):
        # Initialize SPI Communication
        self.CSn = _CSn
        self.csn = Pin(self.CSn, Pin.OUT, value=1)
        self.spi = SPI(_SPI_ID, sck=Pin(_sck), mosi=Pin(_mosi), miso=Pin(_miso), baudrate=_baudrate, polarity=_polarity, phase=_phase, bits=_bits, firstbit=_firstbit)
        self.sendCommand = bytearray(b'\xc0\x00')
        self.receivedData = bytearray(2)
        self.buff_command = bytearray(2)
        self.buff_contentFrame = bytearray(2)
        self.tclk_2_us = 1000000 // (_baudrate * 2) + 1  # Tclk / 2 us

    def __del__(self):
        try:
            self.spi.deinit()
        except:
            pass
        self.csn = Pin(self.CSn, Pin.IN, pull=None)

    def writeData(self, command, value):
        # Send command
        self.csn.off()
        #time.sleep_us(1)
        self.spi.write(command)
        time.sleep_us(self.tclk_2_us)
        self.csn.on()

        #time.sleep_us(1)

        # Send data
        self.csn.off()
        #time.sleep_us(1)
        self.spi.write(value)
        time.sleep_us(self.tclk_2_us)
        self.csn.on()

    def readData(self, command):
        # Send Read Command
        self.sendCommand = uctypes.bytes_at(uctypes.addressof(command), uctypes.sizeof(command))
        self.csn.off()
        #time.sleep_us(1)
        self.spi.write(self.sendCommand)
        time.sleep_us(self.tclk_2_us)
        self.csn.on()

        #time.sleep_us(1)

        # Send Nop Command while receiving data
        self.csn.off()
        #time.sleep_us(1)
        self.spi.write_readinto(bytes(b'\xc0\x00'), self.receivedData)
        time.sleep_us(self.tclk_2_us)
        self.csn.on()

        return self.receivedData

    def readDataAgain(self):
        self.csn.off()
        #time.sleep_us(1)
        self.spi.write_readinto(self.sendCommand, self.receivedData)
        time.sleep_us(self.tclk_2_us)
        self.csn.on()

        return self.receivedData

    def readRegister(self, registerAddress):
        self.command = uctypes.struct(uctypes.addressof(self.buff_command), Command_Frame_struct, uctypes.BIG_ENDIAN)
        self.command.ADDR = registerAddress
        self.command.R_W = READ
        self.command.PARC = isEven(int.from_bytes(self.buff_command, 'big'), MSB_mask)

        receivedFrame = self.readData(self.command)

        return uctypes.struct(uctypes.addressof(receivedFrame), Read_Data_Frame_struct, uctypes.BIG_ENDIAN)

    def newDataFrame(self):
        return uctypes.struct(uctypes.addressof(bytearray(b'00')), Read_Data_Frame_struct, uctypes.BIG_ENDIAN)

    def readRegisterAgain(self):
        receivedFrame = self.readDataAgain()
        return uctypes.struct(uctypes.addressof(receivedFrame), Read_Data_Frame_struct, uctypes.BIG_ENDIAN)

    def writeRegister(self, registerAddress, registerValue):
        command = uctypes.struct(uctypes.addressof(self.buff_command), Command_Frame_struct, uctypes.BIG_ENDIAN)
        command.ADDR = registerAddress
        command.R_W = WRITE
        command.PARC = isEven(int.from_bytes(self.buff_command, 'big'), MSB_mask)

        contentFrame = uctypes.struct(uctypes.addressof(self.buff_contentFrame), Write_Data_Frame_struct, uctypes.BIG_ENDIAN)
        contentFrame.DATA = registerValue
        contentFrame.LOW = 0
        contentFrame.PARD = isEven(int.from_bytes(self.buff_contentFrame, 'big'), MSB_mask)

        self.writeData(command, contentFrame)

    def readAngle(self):
        readDataFrame = self.readRegister(ANGLEUNC)
        angle = uctypes.struct(uctypes.addressof(readDataFrame), ANGLEUNC_struct, uctypes.BIG_ENDIAN)
        return angle.CORDICANG * 360 / 0x4000

    def readAngleAgain(self):
        readDataFrame = self.readRegisterAgain()
        angle = uctypes.struct(uctypes.addressof(readDataFrame), ANGLEUNC_struct, uctypes.BIG_ENDIAN)
        return angle.CORDICANG * 360 / 0x4000

    def readAngleCom(self):
        readDataFrame = self.readRegister(ANGLECOM)
        angle = uctypes.struct(uctypes.addressof(readDataFrame), ANGLECOM_struct, uctypes.BIG_ENDIAN)
        return angle.DAECANG * 360 / 0x4000

    def readAngleComAgain(self):
        readDataFrame = self.readRegisterAgain()
        angle = uctypes.struct(uctypes.addressof(readDataFrame), ANGLECOM_struct, uctypes.BIG_ENDIAN)
        return angle.DAECANG * 360 / 0x4000

    def writeSettings1(self, value):
        self.writeRegister(SETTINGS1, value)

    def writeSettings2(self, value):
        self.writeRegister(SETTINGS2, value)

    def writeZeroPosition(self, zposm, zposl):
        self.writeRegister(ZPOSM, zposm)
        self.writeRegister(ZPOSL, zposl)


def printDebugString(as5x47):
    print("======== AS5X47 Debug ========")

    readDataFrame = as5x47.readRegister(ERRFL)
    errfl = uctypes.struct(uctypes.addressof(readDataFrame), ERRFL_struct, uctypes.BIG_ENDIAN)
    print("------- ERRFL Register :")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   FRERR: ", errfl.FRERR)
    print("|   INVCOMM: ", errfl.INVCOMM)
    print("|   PARERR: ", errfl.PARERR)

    readDataFrame = as5x47.readRegister(PROG)
    prog = uctypes.struct(uctypes.addressof(readDataFrame), PROG_struct, uctypes.BIG_ENDIAN)
    print("------- PROG Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   PROGEN: ", prog.PROGEN)
    print("|   OTPREF: ", prog.OTPREF)
    print("|   PROGOTP: ", prog.PROGOTP)
    print("|   PROGVER: ", prog.PROGVER)

    readDataFrame = as5x47.readRegister(DIAAGC)
    diaagc = uctypes.struct(uctypes.addressof(readDataFrame), DIAAGC_struct, uctypes.BIG_ENDIAN)
    print("|------- DIAAGC Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   AGC: ", diaagc.AGC)
    print("|   LF: ", diaagc.LF)
    print("|   COF: ", diaagc.COF)
    print("|   MAGH: ", diaagc.MAGH)
    print("|   MAGL: ", diaagc.MAGL)

    readDataFrame = as5x47.readRegister(MAG)
    mag = uctypes.struct(uctypes.addressof(readDataFrame), MAG_struct, uctypes.BIG_ENDIAN)
    print("|------- MAG Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   CMAG: ", mag.CMAG)

    readDataFrame = as5x47.readRegister(ANGLEUNC)
    angle = uctypes.struct(uctypes.addressof(readDataFrame), ANGLEUNC_struct, uctypes.BIG_ENDIAN)
    print("|------- ANGLE Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   CORDICANG: ", angle.CORDICANG)
    angleCORDICANG = angle.CORDICANG

    DataFrame = as5x47.newDataFrame()
    zposm = uctypes.struct(uctypes.addressof(DataFrame), ZPOSM_struct, uctypes.BIG_ENDIAN)
    zposm.ZPOSM = 0
    #as5x47.writeRegister(ZPOSM, DataFrame.DATA)

    zposl = uctypes.struct(uctypes.addressof(DataFrame), ZPOSL_struct, uctypes.BIG_ENDIAN)
    zposl.ZPOSL = 0
    #as5x47.writeRegister(ZPOSL, DataFrame.DATA)
    as5x47.writeZeroPosition(DataFrame.DATA, DataFrame.DATA)

    readDataFrame = as5x47.readRegister(ANGLEUNC)
    angle = uctypes.struct(uctypes.addressof(readDataFrame), ANGLEUNC_struct, uctypes.BIG_ENDIAN)
    print("|------- ANGLE Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   CORDICANG: ", angle.CORDICANG)
    angleCORDICANG = angle.CORDICANG

    readDataFrame = as5x47.readRegister(ANGLECOM)
    anglecom = uctypes.struct(uctypes.addressof(readDataFrame), ANGLECOM_struct, uctypes.BIG_ENDIAN)
    print("|------- ANGLECOM Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   DAECANG: ", anglecom.DAECANG)

    readDataFrame = as5x47.readRegister(ZPOSM)
    zposm = uctypes.struct(uctypes.addressof(readDataFrame), ZPOSM_struct, uctypes.BIG_ENDIAN)
    print("|------- ZPOSM Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   ZPOSM: ", zposm.ZPOSM)

    zposm.ZPOSM = (angleCORDICANG >> 6) & 0xFF
    as5x47.writeRegister(ZPOSM, readDataFrame.DATA)

    readDataFrame = as5x47.readRegister(ZPOSM)
    zposm = uctypes.struct(uctypes.addressof(readDataFrame), ZPOSM_struct, uctypes.BIG_ENDIAN)
    print("|------- ZPOSM Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   ZPOSM: ", zposm.ZPOSM)

    readDataFrame = as5x47.readRegister(ZPOSL)
    zposl = uctypes.struct(uctypes.addressof(readDataFrame), ZPOSL_struct, uctypes.BIG_ENDIAN)
    print("|------- ZPOSL Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   ZPOSL: ", zposl.ZPOSL)
    print("|   COMP_L_ERROR_EN: ", zposl.COMP_L_ERROR_EN)
    print("|   COMP_H_ERROR_EN: ", zposl.COMP_H_ERROR_EN)

    zposl.ZPOSL = angleCORDICANG & 0x3F
    as5x47.writeRegister(ZPOSL, readDataFrame.DATA)

    readDataFrame = as5x47.readRegister(ZPOSL)
    zposl = uctypes.struct(uctypes.addressof(readDataFrame), ZPOSL_struct, uctypes.BIG_ENDIAN)
    print("|------- ZPOSL Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   ZPOSL: ", zposl.ZPOSL)
    print("|   COMP_L_ERROR_EN: ", zposl.COMP_L_ERROR_EN)
    print("|   COMP_H_ERROR_EN: ", zposl.COMP_H_ERROR_EN)

    readDataFrame = as5x47.readRegister(SETTINGS1)
    settings1 = uctypes.struct(uctypes.addressof(readDataFrame), SETTINGS1_struct, uctypes.BIG_ENDIAN)
    print("|------- SETTINGS1 Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   Factory_Setting: ", settings1.FACTORY_SETTING)
    print("|   NOT_USED: ", settings1.NOT_USED)
    print("|   DIR: ", settings1.DIR)
    print("|   UVW_ABI: ", settings1.UVW_ABI)
    print("|   DAECDIS: ", settings1.DAECDIS)
    print("|   ABIBIN: ", settings1.ABIBIN)
    print("|   DATASELECT: ", settings1.DATASELECT)
    print("|   PWMON: ", settings1.PWMON)

    settings1.DIR = 1
    as5x47.writeRegister(SETTINGS1, readDataFrame.DATA)

    readDataFrame = as5x47.readRegister(SETTINGS1)
    settings1 = uctypes.struct(uctypes.addressof(readDataFrame), SETTINGS1_struct, uctypes.BIG_ENDIAN)
    print("|------- SETTINGS1 Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   Factory_Setting: ", settings1.FACTORY_SETTING)
    print("|   NOT_USED: ", settings1.NOT_USED)
    print("|   DIR: ", settings1.DIR)
    print("|   UVW_ABI: ", settings1.UVW_ABI)
    print("|   DAECDIS: ", settings1.DAECDIS)
    print("|   ABIBIN: ", settings1.ABIBIN)
    print("|   DATASELECT: ", settings1.DATASELECT)
    print("|   PWMON: ", settings1.PWMON)

    readDataFrame = as5x47.readRegister(SETTINGS2)
    settings2 = uctypes.struct(uctypes.addressof(readDataFrame), SETTINGS2_struct, uctypes.BIG_ENDIAN)
    print("|------- SETTINGS2 Register: ")
    print("|   Reading Error: ", readDataFrame.EF)
    print("|   UVWPP: ", settings2.UVWPP)
    print("|   HYS: ", settings2.HYS)
    print("|   ABIRES: ", settings2.ABIRES)

    print("==============================")


# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        as5047d = AS5x47()  # _baudrate=10000000
        #as5047d = AS5x47(_SPI_ID=SOFT_SPI_ID, _baudrate=1000000, _polarity=0, _phase=1, _bits=8)  # 10000000
        #as5047d = AS5x47(_SPI_ID=SOFT_SPI_ID, _baudrate=10000, _bits=8)  #
        #as5047d = AS5x47(_SPI_ID=VSPI_ID, _sck=VSPI_sck, _mosi=VSPI_mosi, _miso=VSPI_miso, _baudrate=100000)
        print("readAngleAgain()", as5047d.readAngleAgain())
        printDebugString(as5047d)
        print("readAngleCom()", as5047d.readAngleCom())
        print("readAngle()", as5047d.readAngle())
        print("readAngleAgain()", as5047d.readAngleAgain())
        print("readAngleAgain()", as5047d.readAngleAgain())
        while 1:
            #as5047d.printDebugString()
            #print("AngleCom()", as5047d.readAngleCom())
            #print("Angle()", as5047d.readAngle())
            if 1:
                print("")
                a1 = as5047d.readAngleAgain()
                a2 = as5047d.readAngleAgain()
                a3 = as5047d.readAngleAgain()
                a4 = as5047d.readAngleAgain()
                a5 = as5047d.readAngleAgain()
                print(a1)
                print(a2)
                print(a3)
                print(a4)
                print(a5)
            time.sleep(0.5)
    except:
        raise
    finally:
        #printDebugString(as5047d)
        as5047d.__del__
