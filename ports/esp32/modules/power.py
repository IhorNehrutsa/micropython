MULTIPLIER_V_PoE = 0.7
MULTIPLIER_V_BAT = 0.8

SECONDS_TO_POWER_OFF = 30  # 30s

try:
    import config_power
    MULTIPLIER_V_PoE = config_power.MULTIPLIER_V_PoE
    MULTIPLIER_V_BAT = config_power.MULTIPLIER_V_BAT
    SECONDS_TO_POWER_OFF = config_power.SECONDS_TO_POWER_OFF
    del (config_power)
except (ImportError, AttributeError) as e:
    print("ImportError: import config_power: ", e)

from time import sleep_ms
from machine import Pin, ADC
from esp32 import raw_temperature

from esp32_ import LED, PWR_CTRL, ADC_PoE, ADC_BAT, STEP_1, STEP_2, DIR_1, DIR_2
from temperature_conversion import Celsius_from_Fahrenheit

seconds_after_power_off = 0  # секунд после отключения питания

step1 = Pin(STEP_1, Pin.OUT, value=1)  # Pin.IN может создавать дребезг на входах драйверов ШД
step2 = Pin(STEP_2, Pin.OUT, value=1)

dir1 = Pin(DIR_1, Pin.OUT, value=1)
dir2 = Pin(DIR_2, Pin.OUT, value=1)

led = Pin(LED, Pin.OUT, value=1)

pwr = Pin(PWR_CTRL, Pin.OUT, value=0)  # battery off
if SECONDS_TO_POWER_OFF > 0:
    pwr.value(1)  # battery on

adc_PoE = ADC(Pin(ADC_PoE))  # create ADC object on ADC pin
adc_PoE.atten(ADC.ATTN_6DB)  # 6dB attenuation, gives a maximum input voltage of approximately 2.00v

adc_BAT = ADC(Pin(ADC_BAT))
adc_BAT.atten(ADC.ATTN_6DB)

# напряжение на клеммах
def V_PoE():
    return round(2 * adc_PoE.read() * 30 / 4095 * MULTIPLIER_V_PoE, 1) # 30В т.к. бортовая сеть 24-28В

def V_BAT():
    return round(2 * adc_BAT.read() * 12 / 4095 * MULTIPLIER_V_BAT, 1) # 12В т.к. 11.2В максимум для батареи

def esp32_Celsius():
    return round(Celsius_from_Fahrenheit(raw_temperature()), 1)

def power_off():
    pwr.value(0)  # battery off

def off():
    pwr.value(0)  # battery off

def check_PoE():
    global seconds_after_power_off
    if adc_PoE.read() < 500:
        seconds_after_power_off += 1
        print(f'\nPoE IN lost. Seconds to power off:{SECONDS_TO_POWER_OFF - seconds_after_power_off}.')
        if seconds_after_power_off >= SECONDS_TO_POWER_OFF:
            if seconds_after_power_off >= SECONDS_TO_POWER_OFF:
                print('\nSelf battery off.')
                sleep_ms(1000)  # 1s
                pwr.value(0)  # self power off
        led.value(not led.value())
    else:
        if seconds_after_power_off != 0:
            seconds_after_power_off = 0
            print('\nPoE IN is on again.', power_info())
            led.value(1)

def power_info():
    return f'V_PoE():{V_PoE()}V, \tV_BAT():{V_BAT()}V, \tesp32_Celsius():{esp32_Celsius()}°'

def power_test():
    while True:
        print(power_info())
        sleep_ms(1000)

if __name__ == "__main__":
    power_test()
