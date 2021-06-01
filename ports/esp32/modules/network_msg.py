from gc import collect
collect()
from network import AUTH_OPEN, AUTH_WEP, AUTH_WPA_PSK, AUTH_WPA2_PSK, AUTH_WPA_WPA2_PSK, \
    STAT_IDLE, STAT_CONNECTING, STAT_GOT_IP, \
    STAT_BEACON_TIMEOUT, STAT_NO_AP_FOUND, STAT_WRONG_PASSWORD, STAT_ASSOC_FAIL, STAT_HANDSHAKE_TIMEOUT
collect()

# wlan.scan() authmode messages are:
_AUTHMODE = {
    AUTH_OPEN: "OPEN",  # 0
    AUTH_WEP: "WEP",  # 1
    AUTH_WPA_PSK: "WPA-PSK",  # 2
    AUTH_WPA2_PSK: "WPA2-PSK",  # 3
    AUTH_WPA_WPA2_PSK: "WPA/WPA2-PSK",  # 4
    5: "WPA2-ENTERPRISE",  # 5
    6: "WPA3-PSK",  # 6
    7: "WPA2/WPA3-PSK",  # 7
    # WPA3-192-???
    # OWE-???
    }


@micropython.native
def authmode(x: int):
    try:
        return "{}:{}".format(x, _AUTHMODE[x])
    except KeyError:
        return "_AUTHMODE[{}]-unnown message".format(x)


# wlan.status() messages are:
_WLAN_STATUS = {
    STAT_IDLE: 'STAT_IDLE',  # 1000
    STAT_CONNECTING: 'STAT_CONNECTING',  # 1001
    STAT_GOT_IP: 'STAT_GOT_IP',  # 1010
    STAT_BEACON_TIMEOUT: 'STAT_BEACON_TIMEOUT',  # 200
    STAT_NO_AP_FOUND: 'STAT_NO_AP_FOUND',  # 201
    STAT_WRONG_PASSWORD: 'STAT_WRONG_PASSWORD',  # 202
    STAT_ASSOC_FAIL: 'STAT_ASSOC_FAIL',  # 203
    STAT_HANDSHAKE_TIMEOUT: 'STAT_HANDSHAKE_TIMEOUT',  # 204
    None: 'STARTED AS ACCESS POINT',  #
    }


@micropython.native
def wlan_status(x: int):
    # USE: wlan_status(wlan.status())
    try:
        return "{}:{}".format(x, _WLAN_STATUS[x])
    except KeyError:
        return "_WLAN_STATUS[{}]-unnown message".format(x)


@micropython.viper
def rssi(dBm: int):
    if dBm >= -30:
        return "{}dBm:Amazing".format(dBm)
    if dBm >= -50:
        return "{}dBm:Excellent".format(dBm)
    if dBm >= -60:
        return "{}dBm:Good".format(dBm)
    if dBm >= -67:
        return "{}dBm:Reliable".format(dBm)
    if dBm >= -79:
        return "{}dBm:Fair".format(dBm)

    if dBm <= -110:
        return "{}dBm:No signal".format(dBm)
    if dBm <= -100:
        return "{}dBm:Poor/Weak".format(dBm)
    if dBm <= -90:
        return "{}dBm:Unusable".format(dBm)
    if dBm <= -80:
        return "{}dBm:Unreliable".format(dBm)


'''
-30 dBm – (Amazing)    Maximum signal strength, you are probably standing right next to the access point.
-50 dBm – (Excellent)  Anything down to this level can be considered excellent signal strength.
-60 dBm – (Good)       Good, reliable signal strength.
–67 dBm – (Reliable)   Reliable signal strength. The minimum for any service depending on a reliable connection and signal strength, such as voice over Wi-Fi and non-HD video streaming. 
-70 dBm – (Fair)       Not a strong signal. Light browsing and email.
-80 dBm – (Unreliable) Unreliable signal strength, will not suffice for most services. Connecting to the network.
-90 dBm – (Unusable)   The chances of even connecting are very low at this level.
###
RSSI(dBm):
       0..-50 (Excellent, Отлично), зеленый
     -50..-60 (Good, Хорошо), желтый
     -60..-70 (Fair, Passably, Удовлетворительно), оранжевый
less then -70 (Weak, Слабо), красный
         -100 (Miss, Absent, Отсутствует) there is no signal at all, фиолетовый
'''
