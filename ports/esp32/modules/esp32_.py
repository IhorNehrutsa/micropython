# ESP32 Pin List # esp32-wroom-32_datasheet_en.pdf
# Внимание! В этом файле числа - это номера GPIO, а не номера физических выводов(пинов).
try:
    from micropython import const
except ImportError:

    def const(x):
        return x


# ----------------------------------------------------------------------
# SPI
# SPI    MOSI   MISO    CLK     CS
# HSPI  GPIO13  GPIO12  GPIO14  GPIO15
# VSPI  GPIO23  GPIO19  GPIO18  GPIO5

HSPI_ID = const(1)  #### hardware                   #  mcp2515
HSPI_sck = const(14)  ## SCL/SCLK #       (GPIO14)  # SCK синий
HSPI_mosi = const(13)  # SDA/SDI  # SI  # (GPIO13)  # SI  зеленый
HSPI_miso = const(12)  # AD0/SDO  # SO  # (GPIO12)  # SO  желтый
HSPI_cs1 = const(15)  ## nCS      # nSS   (GPIO15)  # CS  оранжевый
#HSPI_cs2 = const(18)  ##                            # INT фиолетовый
#HSPI_cs3 = const(19)  ##

# VSPI_ID = 2  # hardware
# VSPI_sck = 18
# VSPI_mosi = 23
# VSPI_miso = 19
# VSPI_cs = 5
#
# SOFT_SPI_ID = -1  # software
# ----------------------------------------------------------------------
# I2C
I2C0_ID = const(0)  # hardware
SCL = const(22)  # 14 # (GPIO22)
SDA = const(21)  # 13 # (GPIO21)

#I2C1_ID = const(1)  # hardware

#SOFT_I2C_ID = const(-1)  # software
# ----------------------------------------------------------------------
# ADC
# ESP32 GPIOs: 0, 2, 4, 12, 13, 14, 15, 25, 26, 27, 32, 33, 34, 35, 36, 39.
# On the ESP32 ADC functionality is available on Pins 32-39
ADC_PoE = const(34)  # (GPIO34)
ADC_BAT = const(35)  # (GPIO35)

PWR_CTRL = const(33)  # (GPIO33)
LED = const(2)  #     # (GPIO02)
# ----------------------------------------------------------------------
# Button
BUT1 = const(36)
BUT2 = const(39)
# ----------------------------------------------------------------------
# DAC
#DAC1 = const(25)  # (GPIO25)
#DAC2 = const(26)  # (GPIO26)
# ----------------------------------------------------------------------
# UART
#U0TXD = const(1)  # used USB/REPL/
#U0RXD = const(3)

#U1TXD = const(4)
#U1RXD = const(5)

#U2TXD = const(17)
#U2RXD = const(16)

#Encoder
#ENCODER_SW = U1RXD  # # orange
#ENCODER_DATA = U2TXD  # yellow
#ENCODER_CLK = U2RXD  ## green
# ----------------------------------------------------------------------
# STEP/DIR MOTOR
STEP_1 = const(26)  # XP14 Azim
DIR_1 = const(23)

STEP_2 = const(27)  # XP15 Elev
DIR_2 = const(32)
# ----------------------------------------------------------------------
#  Input only pins
# GPIO34  input only
# GPIO35  input only
# GPIO36  input only
# GPIO39  input only
# ----------------------------------------------------------------------
# Strapping Pins
# GPIO0
# GPIO2
# GPIO5 (must be HIGH during boot)
# GPIO 12 (MTDI) (must be LOW during boot) (Has internal pull-down)
# GPIO 15 (MTDO) (must be HIGH during boot) (Has an internal pull-up)
# ----------------------------------------------------------------------
# Pins HIGH at Boot
# GPIO1
# GPIO3
# GPIO5
# GPIO6 to GPIO11 (connected to the ESP32 integrated SPI flash memory – not recommended to use).
# GPIO14
# GPIO15
# ----------------------------------------------------------------------
# Used for internal flash, not recommended for other use
# GPIO6 - GPIO11 - 6 выводов
# ----------------------------------------------------------------------
# При разводке дорожек можно менять местами между собой в одной строке(но не между строками):
# GPIO: 18, 19, 23, 26, 27, 32, 33
# GPIO: 36, 39
# GPIO: 34, 35
