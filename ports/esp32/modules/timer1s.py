# timer1s.py

from machine import Timer

import power
import WiFi 


__timer = None
__check_WiFi_connect = False

def __timer1s_callback(timer):
    global __check_WiFi_connect
    if __check_WiFi_connect:
        WiFi.check_WiFi_connect()
    if power.SECONDS_TO_POWER_OFF > 0:
        power.check_PoE()

def timer1s_start(period=1000, check_WiFi_connect=True):
    global __timer
    global __check_WiFi_connect
    __check_WiFi_connect = check_WiFi_connect
    if __check_WiFi_connect or power.SECONDS_TO_POWER_OFF > 0:
        if __timer is None:
            __timer = Timer(-2, mode=Timer.PERIODIC, period=period, callback=__timer1s_callback)

def timer1s_deinit():
    global __timer
    if __timer is not None:
        __timer.deinit() 
        __timer = None

if __name__ == "__main__":
    timer1s_start()
