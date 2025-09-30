from errno import EAGAIN, EINPROGRESS
from json import loads

#from skt import close_socket
from RouterOS_API import open_socket


class MicroPyClient(object):
    CLOSED = 0  # сокет закрыт
    OPENED = 1  # сокет открыт
    SENT = 2  # запрос отправлен
    RECVED = 3  # ответ получен

    def __init__(self, host, port=3232, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._skt = None
        self.data = ""
        self._out = ""
        self._out_index = 0
        self.state = self.CLOSED
        self.empty_bufs()

    def empty_in_buf(self):
        self._in_buf = b""

    def empty_bufs(self):
        self.empty_in_buf()

    def connect_close(self):
        if self._skt is not None:
            print("{}:{} MicroPyClient close socket".format(self.host, self.port), self._skt.fileno())
            self._skt.close()
        self._skt = None
        self.state = self.CLOSED
        self.empty_bufs()

    def __del__(self):
        self.connect_close()

    @property
    def out(self):
        return self._out

    @out.setter
    def out(self, s):
        self._out = s
        self._out_index = 0

    def execute(self):
        if self._skt is None:
            self._skt = open_socket(self.host, port=self.port, timeout=self.timeout, prn=False)
            if self._skt is None:
                return None
            print("{}:{} MicroPyClient open socket".format(self.host, self.port), self._skt.fileno())
            self.state = self.OPENED

        if self.state == self.OPENED:
            if self._out_index < len(self._out):
                try:
                    sent = self._skt.send(bytes(self._out[self._out_index:], "utf-8"))
                    if sent == 0:
                        print("{}:{} MicroPyClient socket {} error: sent == 0".format(self.host, self.port, self._skt.fileno()), sent)
                        self.connect_close()
                        return
                    self._out_index += sent
                    if self._out_index >= len(self._out):
                        self.state = self.SENT
                except Exception as e:
                    if e.args[0] in (EAGAIN, 10035, EINPROGRESS):
                        return
                    print("{}:{} MicroPyClient socket {} error: send:".format(self.host, self.port, self._skt.fileno()), e)
                    self.connect_close()
                    return

        elif self.state == self.SENT:
            try:
                received = self._skt.recv(1024)
                if received == b"":
                    print("{}:{} MicroPyClient socket {} error: received == b''".format(self.host, self.port, self._skt.fileno()))
                    self.connect_close()
                    return
                else:
                    self._in_buf += received
            except Exception as e:
                if e.args[0] in (EAGAIN, 10035, EINPROGRESS):
                    return
                print("{}:{} MicroPyClient socket {} error: receive:".format(self.host, self.port, self._skt.fileno()), e)
                self.connect_close()
                return

            eol_pos = self._in_buf.find(b"\n")
            if eol_pos < 0:
                return
            r = self._in_buf[:eol_pos]
            self._in_buf = self._in_buf[eol_pos + 1:]
            if len(r) <= 0:
                return
            if r == b'HEARTBEAT':
                print('r', r)
                return
            self.data = loads(str(r, "utf-8"))
            self.state = self.RECVED

            eol_pos = self._in_buf.rfind(b"\n")
            if eol_pos >= 0:
                self._in_buf = self._in_buf[eol_pos + 1:]
