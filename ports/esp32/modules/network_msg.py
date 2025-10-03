from network import AUTH_OPEN, AUTH_WEP, AUTH_WPA_PSK, AUTH_WPA2_PSK, AUTH_WPA_WPA2_PSK, \
    AUTH_WPA2_ENTERPRISE, AUTH_WPA3_PSK, AUTH_WPA2_WPA3_PSK, AUTH_WAPI_PSK, AUTH_OWE, \
    AUTH_WPA3_ENT_192, AUTH_WPA3_EXT_PSK, AUTH_WPA3_EXT_PSK_MIXED_MODE, \
    STAT_IDLE, STAT_CONNECTING, STAT_GOT_IP, \
    STAT_NO_AP_FOUND, STAT_NO_AP_FOUND_IN_RSSI_THRESHOLD, STAT_NO_AP_FOUND_IN_AUTHMODE_THRESHOLD, STAT_NO_AP_FOUND_W_COMPATIBLE_SECURITY, \
    STAT_WRONG_PASSWORD, STAT_BEACON_TIMEOUT, STAT_ASSOC_FAIL, STAT_CONNECT_FAIL, STAT_HANDSHAKE_TIMEOUT


# wlan.scan() authmode messages are:
_AUTHMODE = {
    AUTH_OPEN: "OPEN",
    AUTH_WEP: "WEP",
    AUTH_WPA_PSK: "WPA-PSK",
    AUTH_WPA2_PSK: "WPA2-PSK",
    AUTH_WPA_WPA2_PSK: "WPA/WPA2-PSK",
    AUTH_WPA2_ENTERPRISE: "WPA2-ENTERPRISE",
    AUTH_WPA3_PSK: "WPA3-PSK",
    AUTH_WPA2_WPA3_PSK: "WPA2/WPA3-PSK",
    AUTH_WAPI_PSK: "WAPI_PSK",
    AUTH_OWE: "OWE",
    AUTH_WPA3_ENT_192: "WPA3-ENT-192",
    AUTH_WPA3_EXT_PSK: "WPA3-EXT-PSK",
    AUTH_WPA3_EXT_PSK_MIXED_MODE: "WPA3-EXT-PSK-MIXED-MODE",
    }


def authmode(x: int):
    try:
        return "{}:{}".format(x, _AUTHMODE[x])
    except KeyError:
        return "AUTHMODE[{}]-unnown message".format(x)


# wlan.status() messages are:
_WLAN_STATUS = {
    STAT_IDLE: 'STAT_IDLE',
    STAT_CONNECTING: 'STAT_CONNECTING',
    STAT_GOT_IP: 'STAT_GOT_IP',
    STAT_NO_AP_FOUND: 'STAT_NO_AP_FOUND',
    STAT_NO_AP_FOUND_IN_RSSI_THRESHOLD: 'STAT_NO_AP_FOUND_IN_RSSI_THRESHOLD',
    STAT_NO_AP_FOUND_IN_AUTHMODE_THRESHOLD: 'STAT_NO_AP_FOUND_IN_AUTHMODE_THRESHOLD',
    STAT_NO_AP_FOUND_W_COMPATIBLE_SECURITY: 'STAT_NO_AP_FOUND_W_COMPATIBLE_SECURITY',
    STAT_WRONG_PASSWORD: 'STAT_WRONG_PASSWORD',
    STAT_BEACON_TIMEOUT: 'STAT_BEACON_TIMEOUT',
    STAT_ASSOC_FAIL: 'STAT_ASSOC_FAIL',
    STAT_CONNECT_FAIL: 'STAT_CONNECT_FAIL',
    STAT_HANDSHAKE_TIMEOUT: 'STAT_HANDSHAKE_TIMEOUT',
    None: 'STARTED AS ACCESS POINT',
    }


def wlan_status(x: int):
    # USE: wlan_status(wlan.status())
    try:
        return "{}:{}".format(x, _WLAN_STATUS[x])
    except KeyError:
        return "WLAN_STATUS[{}]-unnown message".format(x)


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
-30 dBm - (Amazing)    Maximum signal strength, you are probably standing right next to the access point.
-50 dBm - (Excellent)  Anything down to this level can be considered excellent signal strength.
-60 dBm - (Good)       Good, reliable signal strength.
-67 dBm - (Reliable)   Reliable signal strength. The minimum for any service depending on a reliable connection and signal strength, such as voice over Wi-Fi and non-HD video streaming.
-70 dBm - (Fair)       Not a strong signal. Light browsing and email.
-80 dBm - (Unreliable) Unreliable signal strength, will not suffice for most services. Connecting to the network.
-90 dBm - (Unusable)   The chances of even connecting are very low at this level.
###
RSSI(dBm):
       0..-50 (Excellent, Отлично), зеленый
     -50..-60 (Good, Хорошо), желтый
     -60..-70 (Fair, Passably, Удовлетворительно), оранжевый
less then -70 (Weak, Слабо), красный
         -100 (Miss, Absent, Отсутствует) there is no signal at all, фиолетовый
'''
