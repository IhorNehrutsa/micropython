# WiFi.py
'''
Время загрузки:
Mikrotik mAP ~ 35-45c
Mikrotik RB953GS-5HnT(СРШ-5000) ~ 40c (без Mikrotik mAP)
Mikrotik RB953GS-5HnT(СРШ-5000) ~ 60-70c (последовательно через Mikrotik mAP PoE)
Mikrotik RBM33G(СРШ-5000) ~ 45c (без Mikrotik mAP)
Mikrotik RBM33G(СРШ-5000) ~ 55c (последовательно через Mikrotik mAP PoE)
Mikrotik Dron ~ 45-60c
ESP32 ~ 30-60c
'''
from utime import sleep_ms, time # ticks_ms, ticks_diff,
#from network_msg import wlan_status, authmode, rssi
from sys import print_exception
from _thread import start_new_thread
from machine import Timer
import network
import webrepl

PRINT = False #  True #  

CONNECTING_TIMEOUT = 60 # 60 seconds

SSID = 'TEST_SOVA'
PASSWORD = 'PASSWORD'

DEFAULT_IP = '192.168.1.200'
DEFAULT_SUBNET = '255.255.255.0'
DEFAULT_GATEWAY = '192.168.1.1'
DEFAULT_DNS = DEFAULT_GATEWAY

OWL_IP = 'dhcp'
OWL_SUBNET = ''
OWL_GATEWAY = ''
OWL_DNS = ''

NET_STA_IMPORT = 0

NET_STA_INIT = 1
NET_STA_CONNECTING = 2
NET_STA_GOT_IP = 3
NET_AP_INIT = -1
NET_AP_RUN = -2
NET_AP_GOT_IP = -3

net_state = NET_STA_IMPORT
net_time = time()

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_status = None

ssid_list = []

def save_config_WiFi(ssid, password, ifconfig):
    try:
        print("Save './config_WiFi.py'")
        with open("./config_WiFi.py", "w") as f:
            f.write(f"SSID = '{ssid}'  # internal Sova Mikrotik WiFi\n")
            f.write(f"PASSWORD = '{password}'\n\n")
            f.write(f"OWL_IP = '{ifconfig[0]}'\n")
            f.write(f"#OWL_IP = 'dhcp'\n")
            f.write(f"OWL_SUBNET = '{ifconfig[1]}'\n")
            f.write(f"OWL_GATEWAY = '{ifconfig[2]}'\n")
            f.write(f"OWL_DNS = '{ifconfig[3]}'\n")
            f.close()
    except BaseException as e:
        print_exception(e)
        print('Error writing config_WiFi.py')

def WiFi_info():
    global net_state, net_time
    if net_state >= 0:
        return (net_state, wlan_sta.status(), wlan_sta.active(), wlan_sta.isconnected(), wlan_sta.ifconfig(), time() - net_time)
    else:
        return (net_state, wlan_ap.status(), wlan_ap.active(), wlan_ap.isconnected(), wlan_ap.ifconfig(), time() - net_time)

def WiFi_connect(prn=False):
    global PRINT
    global wlan_sta, wlan_status
    global SSID, PASSWORD
    global OWL_IP, OWL_SUBNET, OWL_GATEWAY, OWL_DNS
    global DEFAULT_IP, DEFAULT_SUBNET, DEFAULT_GATEWAY, DEFAULT_DNS
    global net_state, net_time
    
    if prn:
        PRINT = prn

    if net_state == NET_STA_IMPORT:
        try:
            import config_serial
            if type(config_serial.SERIAL_NUMBER) is str:
                config_serial_SERIAL_NUMBER = int(config_serial.SERIAL_NUMBER)
            else:
                config_serial_SERIAL_NUMBER = config_serial.SERIAL_NUMBER
            if config_serial_SERIAL_NUMBER > 0:
                ip4 = 100 + config_serial_SERIAL_NUMBER % 100
                DEFAULT_IP = DEFAULT_IP[:DEFAULT_IP.rfind('.') + 1] + str(ip4)
            del config_serial
        except (ImportError, AttributeError) as e:
            print_exception(e)

        try:
            import config_WiFi
            SSID = config_WiFi.SSID
            PASSWORD = config_WiFi.PASSWORD
            OWL_IP = config_WiFi.OWL_IP
            OWL_SUBNET = config_WiFi.OWL_SUBNET
            OWL_GATEWAY = config_WiFi.OWL_GATEWAY
            OWL_DNS = config_WiFi.OWL_DNS
            del config_WiFi
        except (ImportError, AttributeError) as e:
            print_exception(e)
            OWL_IP = 'dhcp'

        network.hostname('ESP-' + SSID.replace(' ','_'))

        if OWL_IP.lower() == 'dhcp':
            PRINT and print('import', SSID, PASSWORD, OWL_IP)
        else:
            PRINT and print('import', SSID, PASSWORD, OWL_IP, OWL_SUBNET, OWL_GATEWAY, OWL_DNS)
        net_state = NET_STA_INIT
        PRINT and print('NET_STA_INIT: import')

    if net_state == NET_STA_INIT:
        if wlan_ap.active():
            wlan_ap.active(False)
        if wlan_sta.config('ssid') != SSID:
            if wlan_sta.isconnected():
                wlan_sta.disconnect()
                PRINT and print('wlan_sta.disconnect()')

        if OWL_IP.lower() == 'dhcp':
            if wlan_sta.ifconfig()[0] != '0.0.0.0':
                if wlan_sta.isconnected():
                    wlan_sta.disconnect()
                wlan_sta.ifconfig(('dhcp'))
        else:
            wlan_sta.ifconfig((OWL_IP, OWL_SUBNET, OWL_GATEWAY, OWL_DNS))
        wlan_sta.active(True)
        if not wlan_sta.isconnected():
            PRINT and print('connecting to network...', SSID)
            PRINT and print(WiFi_info())
            try:
                wlan_sta.connect(SSID, PASSWORD)
            except:
                try:
                    wlan_sta.connect()
                except:
                    pass
        net_time = time()
        net_state = NET_STA_CONNECTING
        PRINT and print('NET_STA_CONNECTING: INIT')
    elif net_state == NET_STA_CONNECTING:
        if wlan_sta.status() == network.STAT_GOT_IP:
            net_state = NET_STA_GOT_IP
            PRINT and print('NET_STA_GOT_IP')
        else:
            if time() - net_time >= CONNECTING_TIMEOUT * 3:
                net_state = NET_AP_INIT
                PRINT and print('NET_AP_INIT: not STAT_GOT_IP')
            elif time() - net_time >= CONNECTING_TIMEOUT:
                if wlan_sta.status() != network.STAT_NO_AP_FOUND:
                    if OWL_IP != DEFAULT_IP:
                        OWL_IP, OWL_SUBNET, OWL_GATEWAY, OWL_DNS = DEFAULT_IP, DEFAULT_SUBNET, DEFAULT_GATEWAY, DEFAULT_DNS
                        net_state = NET_STA_INIT
                        PRINT and print('NET_STA_INIT: DEFAULT_IP')
    elif net_state == NET_STA_GOT_IP:
        if wlan_sta.status() != network.STAT_GOT_IP:
            net_state = NET_STA_CONNECTING
            PRINT and print('NET_STA_CONNECTING: not STAT_GOT_IP')
    elif net_state == NET_AP_INIT:
        if wlan_sta.active():
            if wlan_sta.isconnected():
                wlan_sta.disconnect()
            ### wlan_sta.active(False)
        wlan_ap.active(True)
        wlan_ap.config(ssid='ESP-AP-' + SSID)
        wlan_ap.config(max_clients=5)
        net_time = time()
        net_state = NET_AP_RUN
        PRINT and print('NET_AP_RUN')
    elif net_state == NET_AP_RUN:
        if not wlan_ap.isconnected():
            if time() - net_time >= CONNECTING_TIMEOUT * 2:
                net_state = NET_STA_INIT
                PRINT and print('NET_STA_INIT: AP TIMEOUT')

    #if not wlan_sta.active():
#     if not wlan_sta.isconnected():
#         if net_state > NET_STA_INIT:
#             net_state = NET_STA_INIT
#             PRINT and print('NET_STA_INIT')

    if wlan_status != wlan_sta.status():
        PRINT and print('wlan_sta.status()', wlan_status, 'changed to', wlan_sta.status(), wlan_sta.active(), wlan_sta.isconnected(), wlan_sta.ifconfig())
        wlan_status = wlan_sta.status()

    if wlan_status == network.STAT_NO_AP_FOUND:
        if net_state >= NET_STA_INIT:
            if time() - net_time >= CONNECTING_TIMEOUT * 3:
                net_state = NET_AP_INIT
                PRINT and print('NET_AP_INIT: STAT_NO_AP_FOUND')
    elif wlan_status == network.STAT_GOT_IP:
        if net_state != NET_STA_GOT_IP:
#             try:
#                 webrepl.stop()
#             except:
#                 pass
            webrepl.start(password='')
            net_state = NET_STA_GOT_IP
            PRINT and print('NET_STA_GOT_IP')

    return WiFi_info()

def host(host=""):
    if host in ("", "localhost", "127.0.0.1", "127.0.0.0/8", "0.0.0.0"):
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            wlan = network.WLAN(network.AP_IF)
        return wlan.ifconfig()[0]
    else:
        return host

__wifi_info = None

def check_WiFi_connect(timer=None):
    global __wifi_info
    WiFi_connect()
    i = WiFi_info()
    if __wifi_info is None or __wifi_info[:-1] != i[:-1]:
        __wifi_info = i
        PRINT and print(i)

__scan_time = 0

def WiFi_scan():
    global wlan_ap, wlan_sta
    global ssid_list, __scan_time
    if wlan_ap.active():
        if time() - __scan_time >= 15:
            __scan_time = time()
            ssid_list = []
            wlan_sta.active(False)  # ???
            wlan_sta.active(True)  # ???
            scan = wlan_sta.scan()
            #print('scan', scan)
            for s in scan:
                if len(s[0]):
                    ssid_list.append(s[0].decode())
                    #print('s[0].decode()', s[0].decode())
        
    
def WiFi_test(prn=True):
    global PRINT
    PRINT = prn
    if __wifi_info is None:
        timer = Timer(-2, mode=Timer.PERIODIC, period=1000, callback=check_WiFi_connect)
        print('WiFi_test()')

if __name__ == "__main__":
    WiFi_test()
#     while 1:
#         WiFi_scan()
    