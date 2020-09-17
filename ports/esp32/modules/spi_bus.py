from machine import SPI, Pin


class SPI_BUS:
    def __init__(self, SS, SS_deselect_value=1, SPI_ID=None, sck=None, mosi=None, miso=None, baudrate=10000000, polarity=0, phase=1, bits=-16, firstbit=SPI.MSB):
        assert SS_deselect_value in [0, 1], "Value 0 and 1 are acceptable"
        assert polarity in [0, 1]
        assert phase in [0, 1]
        assert firstbit in [SPI.MSB, SPI.LSB]
        assert type(SS) is int, "SS must be an integer pin number"

        self.SS_deselect_value = SS_deselect_value
        self.SS = SS  # a pin number
        self.ss = Pin(self.SS, Pin.OUT, value=SS_deselect_value)  # the Pin() object
        self.spi = SPI(SPI_ID, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso), baudrate=baudrate, polarity=polarity, phase=phase, bits=bits, firstbit=firstbit)

    def __del__(self):
        self.deinit()

    def deinit(self):
        try:
            self.deselect()  # 1
        except:
            pass
        try:
            self.spi.deinit()  # 2
        except:
            pass
        try:
            self.ss = Pin(self.CSn, Pin.IN, pull=None)  # 3
            self.ss = None  # 4
        except:
            pass

    def select(self):
        # select slave
        self.ss.value((self.SS_deselect_value ^ 1) & 1)

    def deselect(self):
        # deselect slave
        self.ss.value(self.SS_deselect_value)
