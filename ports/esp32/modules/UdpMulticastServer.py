import uasyncio as asyncio
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
TIMEOUT = 0  # non-blocking for polling, asyncio uses its own scheduling

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
                #self.skt.settimeout(None)
                self.skt.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                # Join multicast group
                self.skt.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, pack(">4s4s", inet_aton(self.multicast_ip), inet_aton(self.server_ip)))
                self.skt.bind((self.multicast_ip, self.multicast_port))
                self.skt.settimeout(self.timeout)
                if PRINT: print('UdpMulticastServer:bind:', self.multicast_ip, self.multicast_port)
        except Exception as e:
            print_exception(e)
            self.skt = None

    def end(self):
        try:
            if self.skt:
                self.skt.close()
        except:
            pass
        self.skt = None

    def _prepare_response(self):
        """Internal helper to format the response string."""
        return f'Mac${self.mac};Type:SOVA;IP:{self.server_ip};SovaName:{self.owl.SSID};RRS_IP:{self.owl.ROUTEROS_IP};'

    def _check_connection(self):
        """Ensures socket is active and IP hasn't changed."""
        if self.host != self.server_ip:
            self.end()
        if self.skt is None and self.server_ip is not None:
            self.begin()
        return self.skt is not None

    # --- Synchronous Version ---
    def execute(self):
        if not self._check_connection():
            return

        try:
            received, addr = self.skt.recvfrom(128)
            if received:
                if PRINT: print(f'GET from {addr}\t received "{received.decode()}"')
            if received == b'GET':
                sleep_ms(randrange(1, SLEEP_RANDOM_MS))
                msg = self._prepare_response()
                self.skt.sendto(msg, (self.multicast_ip, self.multicast_port))
                if PRINT: print(f'ACK to   {(self.multicast_ip, self.multicast_port)}\t sent     "{msg}"')
        except OSError as e:
            if e.args[0] not in (EAGAIN, ETIMEDOUT):
                print_exception(e)
                self.end()
                raise(e)

    # --- Asynchronous Version ---
    async def async_execute(self):
        while True:
            if not self._check_connection():
                await asyncio.sleep(1)
                continue

            try:
                # Use non-blocking read in async loop
                received, addr = self.skt.recvfrom(128)
                if received == b'GET':
                    await asyncio.sleep_ms(randrange(1, SLEEP_RANDOM_MS))
                    msg = self._prepare_response()
                    self.skt.sendto(msg, (self.multicast_ip, self.multicast_port))
                    if PRINT: print(f'Async ACK sent to {self.multicast_ip}')
            except OSError as e:
                if e.args[0] not in (EAGAIN, ETIMEDOUT):
                    print_exception(e)
                    self.end()
            
            # Yield control back to the event loop
            await asyncio.sleep(0.1)
