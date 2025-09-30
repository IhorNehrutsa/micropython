#!/usr/bin/python3
# -*- coding: latin-1 -*-
from gc import collect

collect()
from socket import socket, getaddrinfo, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

collect()
import sys, binascii, hashlib
from time import time

collect()

from skt import close_socket

collect()

if sys.implementation.name == "micropython":
    is_micropython = True
    from uerrno import EAGAIN, ETIMEDOUT, ECONNRESET, EINPROGRESS
    collect()
else:
    is_micropython = False
    from errno import EAGAIN, ETIMEDOUT, ECONNRESET, EINPROGRESS
    collect()

from re import compile

collect()


class ApiRos:
    "RouterOS API"
    INIT = 0  # after init
    READY = 1
    SEND = 2
    RECV = 3
    HANDLE = 4
    OK = 5
    LOST = 6  # lost connection in wireless bridge
    ERROR = 7  # and upper

    def __init__(self, skt, timeout=None):
        self.name = 'ROS'
        self.skt = skt
        self.ee = None
        self.state = self.INIT
        self.command = None
        self.radio_name = None
        self.params = None
        self.value = None

        self.timeout = timeout

        self.last_closed_ms = None

        self.communication_state = 0

        self.out_buf = bytearray(1024)
        self.out_buf_mv = memoryview(self.out_buf)

        #self.in_buf = bytearray(1024 * 5)
        #self.in_buf_mv = memoryview(self.in_buf)

        self.empty_bufs()
        self.t = 0

    def empty_out_buf(self):
        self.out_index_load = 0  # position to load to self.out_buf
        self.out_index_send = 0  # position to send from self.out_buf by self.skt.send()

    def empty_in_buf(self):
        self.in_buf = b""
        self.in_index_get = 0  ## position to get from self.in_buf
        #self.in_index_load = 0  # position to load to self.in_buf by self.skt.recv()

    def empty_bufs(self):
        self.empty_in_buf()
        self.empty_out_buf()

    def settimeout(self, timeout):
        try:
            self.skt.settimeout(timeout)
            self.timeout = timeout
        except:
            pass

    def close_socket(self):
        try:
            close_socket(self.skt)
        except:
            pass
        self.skt = None
        self.value = None
        self.empty_bufs()

    def login(self, username, pwd):
        if self.skt is None:
            return False
        try:
            self.skt.settimeout(5)
            for repl, attrs in self.talk(["/login", "=name=" + username, "=password=" + pwd]):
                print(f'repl>{repl}<, attrs>{attrs}<, username>{username}<')
                if repl == "!trap":
                    return False
                elif "=ret" in attrs.keys():
                    chal = binascii.unhexlify((attrs["=ret"]).encode())
                    md = hashlib.md5()
                    md.update(b"\x00")
                    md.update(pwd.encode())
                    md.update(chal)
                    for repl2, attrs2 in self.talk(["/login", "=name=" + username, "=response=00" + binascii.hexlify(md.digest()).decode()]):
                        print(f'repl2>{repl}<, attrs2>{attrs2}<')
                        if repl2 == "!trap":
                            return False
            print("RouterOS logged:", username)
            self.state = self.READY
            self.skt.settimeout(0)
            return True
        except Exception as e:
            print(f'login() e>{e}<, e.args[0]>{e.args[0]}< username>{username}<')
            if e.args[0] not in (EAGAIN, ETIMEDOUT, 10035):
                self.ee = e
                self.state = self.ERROR + 1
                self.close_socket()
                return False
            self.skt.settimeout(0)

    def talk(self, words):
        r = []
        if len(words) == 0:
            return r
        self.writeSentence(words)
        #print(words)
        while True:
            response = self.readSentence()
            #print(response)
            if len(response) == 0:
                continue
            reply = response[0]
            attrs = {}
            for w in response[1:]:
                j = w.find("=", 1)
                if j == -1:
                    attrs[w] = ""
                else:
                    attrs[w[:j]] = w[j + 1:]
            r.append((reply, attrs))
            if reply == "!done":
                return r

    def writeSentence(self, words):  # words is List or Tuple
        for w in words:
            self.writeWord(w)
        self.writeWord("")

    def writeString(self, str_):
        self.writeWord(str_)
        self.writeWord("")

    def writeWord(self, str_):
        self.writeLen(len(str_))
        self.writeStr(str_)

    def writeLen(self, l):
        if l < 0x80:
            self.writeByte(l.to_bytes(1, sys.byteorder))
        elif l < 0x4000:
            l |= 0x8000
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        elif l < 0x200000:
            l |= 0xC00000
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        elif l < 0x10000000:
            l |= 0xE0000000
            self.writeByte(((l >> 24) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        else:
            self.writeByte((0xF0).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 24) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))

    def writeByte(self, bytes_):
        #if self.timeout == 0:
        if 0:
            new_index = self.out_index_load + len(bytes_)
            self.out_buf_mv[self.out_index_load:new_index] = bytes_
            self.out_index_load = new_index
        else:
            n = 0
            len_ = len(bytes_)
            mv = memoryview(bytes_)
            while n < len_:
                sent = self.skt.send(mv[n:])
                if sent <= 0:
                    raise RuntimeError(ECONNRESET)
                n += sent

    def writeStr(self, str_):
        self.writeByte(bytes(str_, "UTF-8"))

    def readByte(self):
        #if self.timeout == 0:
        if 0:
            #self.in_buf_mv = memoryview(self.in_buf)
            #received = self.in_buf_mv[self.in_index_get:self.in_index_get + 1]
            received = self.in_buf[self.in_index_get:self.in_index_get + 1]
            self.in_index_get += 1
        else:
            received = self.skt.recv(1)
            if received == b'':
                raise RuntimeError(ECONNRESET)
        #print('readByte() received', received,  int.from_bytes(received, 'big'))
        if is_micropython:
            return int.from_bytes(received, 'big')
        else:
            return int.from_bytes(received, byteorder='big')

    def readStr(self, length):
        ret = b""
        while length > 0:
            #if self.timeout == 0:
            if 0:
                #self.in_buf_mv = memoryview(self.in_buf)
                #received = self.in_buf_mv[self.in_index_get:self.in_index_get + length]
                received = self.in_buf[self.in_index_get:self.in_index_get + length]
                self.in_index_get += length
            else:
                received = self.skt.recv(length)
                if received == b'':
                    raise RuntimeError(ECONNRESET)
            #print('readStr() received', received)
            length -= len(received)
            ret += received
        return ret.decode("UTF-8", "replace")

    def readLen(self) -> int:
        c = self.readByte()
        if (c & 0x80) == 0x00:
            return c
        elif (c & 0xC0) == 0x80:
            return ((c & ~0xC0) << 8) + self.readByte()
        elif (c & 0xE0) == 0xC0:
            c &= ~0xE0
            c <<= 8
            c += self.readByte()
            c <<= 8
            c += self.readByte()
        elif (c & 0xF0) == 0xE0:
            c &= ~0xF0
            c <<= 8
            c += self.readByte()
            c <<= 8
            c += self.readByte()
            c <<= 8
            c += self.readByte()
        elif (c & 0xF8) == 0xF0:
            c = self.readByte()
            c <<= 8
            c += self.readByte()
            c <<= 8
            c += self.readByte()
            c <<= 8
            c += self.readByte()
        return c

    def readWord(self):
        return self.readStr(self.readLen())

    def readSentence(self):
        r = []
        while True:
            w = self.readStr(self.readLen())
            if w == "":
                return r
            r.append(w)

    def readResponse(self):
        res_list = []
        while True:
            response = self.readSentence()
            if response[0] == '!done':
                #print("    Command complete: done")
                break
            else:
                res_list.append(response)
                #print("    ", end='')
                #print(response)
        return res_list

    def receive(self):
        try:
            received = self.skt.recv(1024)  #1024*10)#128)#
            if received == b'':
                print(self.name, "Error: received == b''")
                self.close_socket()
                return False
            self.in_buf += received
        except Exception as e:
            if e.args[0] in (EAGAIN, ETIMEDOUT, 10035):
                return False
            else:
                print(f'receive() e>{e}<, e.args[0]>{e.args[0]}<')
                self.ee = e
                print(self.name, "Error: receive:", e)
                self.close_socket()
                return False
        return True

    def send(self):
        if self.skt is not None:
            if self.out_index_send < self.out_index_load:
                try:
                    sent = self.skt.send(self.out_buf_mv[self.out_index_send:self.out_index_load])
                    if sent <= 0:
                        print(self.name, "Error: sent<=0:", sent)
                        self.close_socket()
                        return False
                    self.out_index_send += sent
                    if self.out_index_send >= self.out_index_load:
                        self.empty_out_buf()
                        self.state = self.RECV
                    return True
                except Exception as e:
                    if e.args[0] in (EAGAIN, ETIMEDOUT, 10035):
                        return True
                    print(f'send() e>{e}<, e.args[0]>{e.args[0]}<')
                    self.ee = e
                    print(self.name, "Error: send:", e.args[0], e)
                    self.close_socket()
                    return False
            else:
                return True
        return False

    def handle_command(self):
#         print('state, value, skt, out_index_load, out_index_send, in_index_get', self.state, self.value, self.skt, self.out_index_load, self.out_index_send, self.in_index_get)
#         print('type(ee)', type(self.ee))
#         print('ee', self.ee)
        if (self.state in (self.READY, self.OK, self.LOST)) or (time() - self.t  > 1):
            self.t = time()
            try:
                self.writeString(self.command)
                #print(self.state, self.radio_name, self.command)
                self.state = self.SEND
            except Exception as e:
                if e.args[0] not in (EAGAIN, ETIMEDOUT, 10035):
                    print(f'handle_command() e>{e}<, e.args[0]>{e.args[0]}<')
                    self.ee = e
                    sys.print_exception(e)
                    self.state = self.ERROR + 2
                    self.close_socket()
                    return

        if not self.send():
            return

        if self.out_index_load == 0:
            #if self.state == self.RECV:
            if not self.receive():
                return

            if len(self.in_buf) == 0:
                return

            #self_in_buf = bytes(self.in_buf_mv[0:self.in_index_load])
            if (self.in_buf == b"\x05!done\x00"):
                #print('self.LOST')
                self.empty_in_buf()
                self.state = self.LOST
                self.value = {}
                return

            self.value = {}
            #self.in_buf_mv = memoryview(self.in_buf)
            #print("---in_buf---\n", self.in_buf, "\n---in_buf---")
            done_pos = self.in_buf.find(b"\x05!done\x00")
            #if (self.in_buf[0:4] != b"\x03!re") or (done_pos < 0):
            if (done_pos < 0):
                #print("---in_buf---", self.in_buf, "---in_buf---")
                self.state = self.ERROR + 3
                return

            index_radio_name = self.in_buf.find(self.radio_name)
            n = 0
            if index_radio_name > 0:
                new_value = {}
                for param in self.params:
                    index_param = self.in_buf.find(param, index_radio_name)
                    if index_param > 0:
                        try:
                            regex = compile(param + b"[-=A-Za-z0-9]*")
                            element = regex.search(self.in_buf[index_param:]).group(0)
                            val_str = element[len(param):]
                            regex = compile(b"-?[1-9]\d*")
                            val_str = regex.search(val_str).group(0)
                            try:
                                val = int(val_str)
                            except:
                                val = 0
                                print('element', element)
                                print('val_str', val_str)
                            new_value.setdefault(param, val)
                            n += 1
                        except Exception as e:
                            self.state = self.ERROR + 5
                            self.ee = e
                            print("regex.search Exception as e", e.args[0], e)

            #print('n=', n, "===in_buf===\n", self.in_buf, "\n===in_buf===")
            if n == len(self.params):
                self.state = self.OK
                self.ee = None
                self.value = new_value
#                 print("===in_buf===\n", self.in_buf, "\n===in_buf===")
#                 print('self.value', self.value)
            else:
                self.state = self.ERROR + 4
                #self.empty_in_buf()
            self.in_buf = self.in_buf[done_pos + 7:]



open_socket_time = 0 

def open_socket(ip, port=0, secure=False, timeout=None, prn=False):  # timeout in seconds, 0==non blocked, None==blocked
    global open_socket_time
    if time() - open_socket_time < 1:
        return None
    open_socket_time = time()
    if port == 0:
        port = 8729 if secure else 8728

    skt = None
    try:
        addr_info = getaddrinfo(ip, port, AF_INET, SOCK_STREAM)
        af, socktype, proto, _canonname, sockaddr = addr_info[0]
        _skt = socket(af, socktype, proto)
        _skt.settimeout(None)
    except OSError as e:
        print("Error1_:", e.args[0], e)
        _skt = None

    if _skt is not None:
        _skt.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        if secure:
            try:
                import ussl as ssl
                collect()
            except ImportError:
                import ssl
                collect()

            skt = ssl.wrap_socket(_skt, ssl_version=ssl.PROTOCOL_TLSv1_2, ciphers="ADH-AES128-SHA256")
            #skt = ssl.wrap_socket(_skt, ssl_version=ssl.PROTOCOL_TLS)
            #skt = ssl.wrap_socket(_skt)
        else:
            skt = _skt

        try:
            skt.settimeout(timeout)
            skt.connect(sockaddr)
        except OSError as e:
            #print("Error: skt.connect(sockaddr)", e.args[0], e, sockaddr)
            if e.args[0] not in (EINPROGRESS, 10035):
                if prn:
                    print("Error: skt.connect(sockaddr)", e.args[0], e, sockaddr, timeout)
                try:
                    skt.close()
                except:
                    pass
                skt = None

    if prn:
        if skt is None:
            print('Error: Could not open socket', sockaddr, timeout)  # , skt
        else:
            print('Socket is opened', sockaddr, skt.fileno())  # skt,
    return skt
