#!/usr/bin/python3
# -*- coding: latin-1 -*-
t_recv = 0

from usocket import socket, getaddrinfo, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

from utime import sleep, ticks_diff
from utimes import times_ms, times_us, is_micropython

import sys

from re import compile

#import binascii, select

# import ssl
# import posix
#import hashlib

# try:
#     import ure as re
# except:
#     import re

import uerrno

#try:
#    import uctypes as ctypes
#except ImportError:
#    import ctypes

#try:
#   import gc
#except ImportError:
#   pass


class ApiRos:
    "RouterOS API"
    INIT = 0  # after init
    LOST = 1  # lost connection in wireless
    BAD = 2
    OK = 3

    def __init__(self, skt):
        self.skt = skt
        self.e = None
        self.state = self.INIT
        #self.buff = bytearray(1024 * 4)
        self.command = None
        self.radio_name = None
        self.params = None
        self.value = None

    def login(self, username, pwd):
        for repl, attrs in self.talk(["/login", "=name=" + username, "=password=" + pwd]):
            if repl == "!trap":
                return False
            elif "=ret" in attrs.keys():
                # for repl, attrs in self.talk(["/login"]):
                chal = binascii.unhexlify((attrs["=ret"]).encode(sys.stdout.encoding))
                md = hashlib.md5()
                md.update(b"\x00")
                md.update(pwd.encode(sys.stdout.encoding))
                md.update(chal)
                for repl2, attrs2 in self.talk([
                    "/login",
                    "=name=" + username,
                    "=response=00" + binascii.hexlify(md.digest()).decode(sys.stdout.encoding),
                    ]):
                    if repl2 == "!trap":
                        return False
        print("Logged:", username)
        return True

    def talk(self, words):
        r = []
        if len(words) == 0:
            return r
        writeSentence(self.skt, words)
        while True:
            response = self.readSentence()
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
            if reply == "!done":
                return r
            r.append((reply, attrs))

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

    def readSentence(self):
        r = []
        while True:
            w = readStr(self.skt, readLen(self.skt))
            if w == "":
                return r
            r.append(w)


#     @micropython.native
#     def readAll(self):
#         res = b""
#         writeSentence(self.skt, self.command)
#         t = times_ms()
#         while ((times_ms() - t) < 100) and (res[-7:] != b"\x05!done\x00"):
#             try:
#                 res += self.skt.recv(1024)  #  * 4
#                 #print("===res===", res, "===res===")
#             except Exception as e:
#                 if e.args[0] != uerrno.EAGAIN:
#                     print("readAll Exception as e", e.args[0], e)
#                     #print("===res===", res, "===res===")
#                     self.state = self.BAD
#                     return b""
#                 # continue AGAIN
#         if (res == b"\x05!done\x00"):
#             self.state = self.LOST
#             return b""
#
#         if (res[0:4] != b"\x03!re") or (res[-7:] != b"\x05!done\x00"):
#             print("res[0:4], res[-7:]", res[0:4], res[0:4] != b"\x03!re", res[-7:], res[-7:] != b"\x05!done\x00")
#             #print("---res---", res, "---res---")
#             self.state = self.BAD
#             return b""
#         self.state = self.OK
#         return res
#
#     #@micropython.native
#     def readAll_bytearray(self):
#         writeSentence(self.skt, self.command)
#         t = times_ms()
#         #res = self.skt.recv(1024 * 2)
#         #res = self.skt.read(1024 * 2)
#         n = 0
#         while n == 0:
#             n = self.skt.readinto(self.buff, len(self.buff))
#             print(n)
#         '''
#         try:
#             res = self.skt.recv(1024 * 3)
#         except:
#             pass
#         while ((times_ms() - t) < 1000) and (res[-7:] != b"\x05!done\x00"):
#             #t1 = times_ms()
#             try:
#                 res += self.skt.recv(1024 * 3)
#             except:
#                 pass
#             #if (times_ms() - t) > 1000:
#             #    raise RuntimeError("Connection closed by remote end 0")
#         '''
#         print("self.buff[0:4], self.buff[n-6:n]", self.buff[0:4], self.buff[n - 6:n])
#         if (self.buff[0:4] != b"\x03!re") or (self.buff[n - 6:n] != b"\x05!done"):
#             print("===", self.buff, "===")
#             return b''
#         print(self.command)
#         return ctypes.bytes_at(ctypes.addressof(self.buff), n)  # len(self.buff))

    @micropython.native
    def handle_command(self):
        self.value = {}

        res = b""
        writeSentence(self.skt, self.command)
        t = times_ms()
        while (ticks_diff(times_ms(), t) < 50) and (res[-7:] != b"\x05!done\x00"):
            try:
                res += self.skt.recv(1024 * 2)  #  * 4
                #print("===res===", res, "===res===")
            except Exception as e:
                self.e = e
                if e.args[0] != uerrno.EAGAIN:
                    #print("handle_command Exception as e", e.args[0], e)
                    #print("===res===", res, "===res===")
                    self.state = self.BAD
                    return
                #else:
                #    pass
                #### continue AGAIN

        if (res == b"\x05!done\x00"):
            self.state = self.LOST
            return

        if (res[0:4] != b"\x03!re") or (res[-7:] != b"\x05!done\x00"):
            #if res[-7:] != b"\x05!done\x00":
            print("res[0:4], res[-7:]", res[0:4], res[0:4] != b"\x03!re", res[-7:], res[-7:] != b"\x05!done\x00")
            #print("---res---", res, "---res---")
            self.state = self.BAD
            return

        index_radio_name = res.find(self.radio_name)
        n = 0
        if index_radio_name > 0:
            for param in self.params:
                index_param = res.find(param, index_radio_name)
                if index_param > 0:
                    try:
                        regex = compile(param + b"[-=A-Za-z0-9]*")
                        element = regex.search(res[index_param:]).group(0)
                        val = int(element[len(param):])
                        self.value.setdefault(param, val)
                        n += 1
                    except Exception as e:
                        self.e = e
                        #print("regex.search Exception as e", e.args[0], e)
                        #pass

        if n == len(self.params):
            self.state = self.OK
            #print(self.value)
        else:
            self.value = {}
            self.state = self.BAD


@micropython.native
def writeSentence(skt, words):
    for w in words:
        writeWord(skt, w)
    writeWord(skt, "")


@micropython.native
def writeByte(skt, str):
    n = 0
    len_str = len(str)
    while n < len_str:
        try:
            r = skt.send(str[n:])
        except Exception as e:
            #return False
            if e.args[0] != uerrno.EAGAIN:
                return False
        if r == 0:
            return False
            raise RuntimeError("Connection closed by remote end 1")
        n += r
    return True


@micropython.native
def writeStr(skt, str):
    n = 0
    len_str = len(str)
    while n < len_str:
        try:
            r = skt.send(bytes(str[n:], "UTF-8"))
        except Exception as e:
            #return False
            if e.args[0] != uerrno.EAGAIN:
                return False
        if r == 0:
            return False
            raise RuntimeError("Connection closed by remote end 2")
        n += r
    return True


@micropython.native
def writeWord(skt, str):
    writeLen(skt, len(str))
    writeStr(skt, str)


@micropython.native
def writeLen(skt, l):
    if l < 0x80:
        writeByte(skt, (l).to_bytes(1, sys.byteorder))
    elif l < 0x4000:
        l |= 0x8000
        tmp = (l >> 8) & 0xFF
        writeByte(skt, ((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, (l & 0xFF).to_bytes(1, sys.byteorder))
    elif l < 0x200000:
        l |= 0xC00000
        writeByte(skt, ((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, ((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, (l & 0xFF).to_bytes(1, sys.byteorder))
    elif l < 0x10000000:
        l |= 0xE0000000
        writeByte(skt, ((l >> 24) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, ((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, ((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, (l & 0xFF).to_bytes(1, sys.byteorder))
    else:
        writeByte(skt, (0xF0).to_bytes(1, sys.byteorder))
        writeByte(skt, ((l >> 24) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, ((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, ((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
        writeByte(skt, (l & 0xFF).to_bytes(1, sys.byteorder))


@micropython.native
def readByte(skt):
    s = skt.recv(1)
    if len(s) == 0:
        raise RuntimeError("Connection closed by remote end 3")
    if is_micropython:
        return int.from_bytes(s, 'big')
    else:
        return int.from_bytes(s, byteorder='big')


@micropython.native
def readStr(skt, length):
    ret = b""
    while length > 0:
        t1 = times_us()

        s = skt.recv(length)

        t2 = times_us()
        global t_recv
        t_recv += (t2 - t1)

        len_s = len(s)
        length -= len_s
        if len_s == 0:
            raise RuntimeError("Connection closed by remote end 4")
        ret += s
    #print(ret)
    return ret.decode("UTF-8", "replace")


@micropython.native
def readWord(skt):
    return readStr(skt, readLen(skt))


@micropython.native
def readLen(skt) -> int:
    c = readByte(skt)
    if (c & 0x80) == 0x00:
        return c
    elif (c & 0xC0) == 0x80:
        return ((c & ~0xC0) << 8) + readByte(skt)
    elif (c & 0xE0) == 0xC0:
        c &= ~0xE0
        c <<= 8
        c += readByte(skt)
        c <<= 8
        c += readByte(skt)
    elif (c & 0xF0) == 0xE0:
        c &= ~0xF0
        c <<= 8
        c += readByte(skt)
        c <<= 8
        c += readByte(skt)
        c <<= 8
        c += readByte(skt)
    elif (c & 0xF8) == 0xF0:
        c = readByte(skt)
        c <<= 8
        c += readByte(skt)
        c <<= 8
        c += readByte(skt)
        c <<= 8
        c += readByte(skt)
    #print (">rl> %i" % c, type(c))
    return c


@micropython.native
def open_socket(ip, port=0, secure=False):
    if port == 0:
        port = 8729 if secure else 8728

    skt = None
    addr_info = getaddrinfo(ip, port, AF_INET, SOCK_STREAM)
    #print("addr_info", addr_info)
    af, socktype, proto, canonname, sockaddr = addr_info[0]
    try:
        _skt = socket(af, socktype, proto)
    except OSError as e:
        print("Error1:", e.args[0], e)
        _skt = None
    if _skt is not None:
        _skt.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        if secure:
            try:
                import ussl as ssl
            except ImportError:
                import ssl

            skt = ssl.wrap_socket(_skt, ssl_version=ssl.PROTOCOL_TLSv1_2, ciphers="ADH-AES128-SHA256")
            #skt = ssl.wrap_socket(_skt, ssl_version=ssl.PROTOCOL_TLS)
            #skt = ssl.wrap_socket(_skt)
        else:
            skt = _skt

        n = 5  # 5
        while (n > 0) and (skt is not None):
            try:
                skt.connect(sockaddr)
                break
            except OSError as e:
                print("Error2:", e.args[0], e)
                print("Try connecting to", sockaddr, "after a 1-second delay", n, "time(s)")
                try:
                    skt.close()
                except:
                    pass
                #skt = None
                sleep(1)
            n -= 1

        if n == 0:
            try:
                skt.close()
            except:
                pass
            skt = None

    if skt is None:
        print('Error: Could not open socket', sockaddr)
    else:
        print('Socket is opened', sockaddr)
    return skt


@micropython.native
def close_socket(skt):
    try:
        skt.close()
    except:
        pass
    print("Socket closed: done")


@micropython.native
def find_in(str, sub, start=0, end=0):
    if end == 0:
        end = len(str)
    f = str.find(sub, start, end)
    return f
