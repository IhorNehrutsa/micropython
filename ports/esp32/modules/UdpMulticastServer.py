from sys import print_exception
from random import randrange
from ubinascii import hexlify
from time import time, sleep_ms
from struct import pack
from network import WLAN, STA_IF, AP_IF
from errno import EAGAIN, ETIMEDOUT
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, IPPROTO_IP, IP_ADD_MEMBERSHIP

PRINT = False

SLEEP_RANDOM_MS = 300 + 1

#TIMEOUT = None  # block
#TIMEOUT = 5  # s
TIMEOUT = 0  # non blocking

MULTICAST_IP = '224.1.11.111'
MULTICAST_PORT = 5555

def inet_aton(str_addr):
    return bytes(map(int, str_addr.split(".")))

class UdpMulticastServer(object):
    def __init__(self, multicast_ip=MULTICAST_IP, multicast_port=MULTICAST_PORT, timeout=TIMEOUT, owl=None):
        self.multicast_ip = multicast_ip
        self.multicast_port = multicast_port
        self.timeout = timeout
        self.owl = owl
        self.server_ip = None
        self.mac = ''
        self.skt = None
        self.t_begin = 0

    def __del__(self):
        self.end()

    @property
    def host(self):
        wlan = WLAN(STA_IF)
        if wlan.isconnected():
            self.server_ip = wlan.ifconfig()[0]
        else:
            wlan = WLAN(AP_IF)
            if wlan.active():
                self.server_ip = wlan.ifconfig()[0]
            else:
                self.server_ip = None
        if self.server_ip is not None:
            self.mac = hexlify(wlan.config('mac'), '-').decode("utf-8").upper()
        return self.server_ip

    def begin(self):
        try:
            if time() - self.t_begin > 0:
                self.t_begin = time()
                self.skt = socket(AF_INET, SOCK_DGRAM)  # UDP
                self.skt.settimeout(None)
                self.skt.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                self.skt.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, pack(">4s4s", inet_aton(self.multicast_ip), inet_aton(self.server_ip)))  # join to the multicast address
                self.skt.bind((self.multicast_ip, self.multicast_port))
                self.skt.settimeout(self.timeout)
        except Exception as e:
            print_exception(e)
            self.skt = None

    def end(self):
        try:
            self.skt.close()
        except:
            pass
        self.skt = None

    def execute(self):
        # Call it in the main loop
        if self.host != self.server_ip:
            self.end()

        if self.skt is None:
            if self.server_ip is not None:
                self.begin()

        if self.skt is None:
            return

        try:
            received, addr = self.skt.recvfrom(128)
            if received:
                PRINT and print(f'GET from {addr}\t received "{received.decode()}"')

                if received == b'GET':
                    sleep_ms(randrange(1, SLEEP_RANDOM_MS))
                    str_to_send = f'Mac${self.mac};Type:SOVA;IP:{self.server_ip};SovaName:{self.owl.SSID};RRS_IP:{self.owl.ROUTEROS_IP};'
                    self.skt.sendto(str_to_send, (self.multicast_ip, self.multicast_port))
                    PRINT and print(f'ACK to   {(self.multicast_ip, self.multicast_port)}\t sent     "{str_to_send}"')
        except OSError as e:
            if e.args[0] in (EAGAIN, ETIMEDOUT):
                pass
            else:
                print_exception(e)
                self.end()
                raise(e)
