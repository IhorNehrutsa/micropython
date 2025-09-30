"""
Based on
MicroPyServer is a simple HTTP server for MicroPython projects.
@see https://github.com/troublegum/micropyserver
"""
import network
from errno import EAGAIN
from io import StringIO
from re import compile
from time import time

from skt import open_server_socket
from uri import URI_percent_decoding

HEARTBEAT = 1  # seconds

# Говорит о том, сколько дескрипторов единовременно могут быть открыты
_BACKLOG = 1  # ???
'''
socket.listen([backlog])
Enable a server to accept connections. If backlog is specified, it must be at least 0 (if it’s lower,
it will be set to 0); and specifies the number of unaccepted connections that the system will allow
before refusing new connections. If not specified, a default reasonable value is chosen.

Разрешить серверу принимать соединения. Если указано отставание , оно должно быть не менее 0 (если меньше,
будет установлено значение 0); и указывает количество непринятых подключений, которое система разрешит
до отказа от новых подключений. Если не указано, выбирается разумное значение по умолчанию.
'''

_method_regexp = compile(b"^([A-Z]+)")
_path_regexp = compile(b"^[A-Z]+\\s+(/[-a-zA-Z0-9_.]*)")
_arg_regexp = compile(b"^[A-Z]+\\s+(/[-a-zA-Z0-9_.\?\&\=%+\(\[,\]\)]*)")


class MicroPyServer(object):
    def __init__(self, host="", port=80, cargo=None):
        self._host = None
        self.port = port

        self._routes = {}
        #self._on_request_handler = None

        self._socket = None  # сокет сервера, слушатель
        self._skt = None  # connection # сокет соединения клиента
        self._client_address = None

        self._success_time = time()

        self.cargo = cargo
        self._request = None

        self.state = 0  # connection is closed
        #            1  # connection established
        #            2  # part or full of the data is received
        #            3  # all response data ready to send

        self.empty_bufs()
        
    @property
    def host(self):
        wlan_sta = network.WLAN(network.STA_IF)
        if wlan_sta.isconnected():
            self._host = wlan_sta.ifconfig()[0]
        else:
            wlan_ap = network.WLAN(network.AP_IF)
            if wlan_ap.active():
                self._host = wlan_ap.ifconfig()[0]
            else:
                self._host = None
        return self._host

    def empty_out_buf(self):
        self._out_buf = b""
        self._out_index = 0

    def empty_in_buf(self):
        self._in_buf = b""

    def empty_bufs(self):
        self.empty_in_buf()
        self.empty_out_buf()

    def __del__(self):
        self.end()

    def find_route(self, request):
        # Find route
        line0 = request.split(b"\r\n")[0]
        method = _method_regexp.search(line0).group(1)
        path = _path_regexp.search(line0).group(1)
        arg = str(URI_percent_decoding(_arg_regexp.search(line0).group(1)), "utf-8")
        try:
            return self._routes[path + b'\x00' + method], arg
        except KeyError as e:
            print("{}:{} MicroPyServer KeyError:{}:".format(self._host, self.port, arg), e)
            return None, arg

    def find_route_txt(self, path):
        # Find route txt
        return self._routes[path + b'\x00GET']

    def begin(self):
        # Call it before the main loop
        try:
            if self.host is not None:
                self._socket = open_server_socket(self._host, self.port, backlog=_BACKLOG)
                print("{}:{} MicroPyServer started".format(self._host, self.port))
        except Exception as e:
            print("{}:{} MicroPyServer error: open_server_socket():".format(self._host, self.port), e)
            self._socket = None  # перестраховка
        return self._socket

    def end(self):
        self.connect_close()
        if self._socket is not None:
            print("{}:{} MicroPyServer close socket".format(self._host, self.port), self._socket.fileno())
            self._socket.close()
            self._socket = None

    def connect_close(self):
        if self._skt is not None:
            #print("{}:{} MicroPyServer close connection".format(self._host, self.port), self._skt.fileno())
            self._skt.close()
        self._skt = None
        self.state = 0
        self.empty_bufs()

    def accept(self):
        try:
            self._skt, self._client_address = self._socket.accept()
            self._skt.settimeout(0)  # non blocking
            #self._skt.settimeout(0.5) # TIMEDOUT
            #self._skt.settimeout(None) # blocking
            #print("{}:{} MicroPyServer accept connection {} from".format(self._host, self.port, self._skt.fileno()), self._client_address)
            self.state = 1
            return True
        except Exception as e:
            if e.args[0] not in (EAGAIN, 10035):
                print("{}:{} MicroPyServer socket {} error: socket.accept():".format(self._host, self.port, self._socket.fileno()), e)
                self.connect_close()
        return False

    def receive(self):
        try:
            received, from_addr = self._skt.recvfrom(1024)
            if received == b'':
                print("{}:{} MicroPyServer connection {} error: received == b'' from {from_addr}".format(self._host, self.port, self._skt.fileno()), from_addr)
                self.connect_close()
                return False
            self._success_time = time()
            self._in_buf += received
            self.state = 2
            return True
        except Exception as e:
            if e.args[0] not in (EAGAIN, 10035):
                print("{}:{} MicroPyServer connection {} error: receive:".format(self._host, self.port, self._skt.fileno()), e)
                self.connect_close()
            return False

    def send(self, do_close):
        if self._skt is not None:
            len_out_buf = len(self._out_buf)
            if self._out_index < len_out_buf:
                try:
                    mv = memoryview(self._out_buf)
                    sent = self._skt.send(mv[self._out_index:])
                    #sent = self._skt.send(mv[self._out_index:min(len_out_buf, self._out_index + 1024 * 2)])
                    #sent = self._skt.send(mv[self._out_index:self._out_index + 1024 * 3])
                    #sent = self._skt.send(mv[self._out_index:self._out_index + 512])
                    #sent = self._skt.send(mv[self._out_index:len_out_buf])
                    if sent == 0:
                        print("{}:{} MicroPyServer connection {} error: sent == 0:".format(self._host, self.port, self._skt.fileno()), sent)
                        self.connect_close()
                        return
                    self._success_time = time()
                    self._out_index += sent
                    if self._out_index >= len_out_buf:
                        self.empty_out_buf()
                        if do_close:
                            self.connect_close()
                except Exception as e:
                    if e.args[0] not in (EAGAIN, 10035):
                        print("{}:{} MicroPyServer connection {} error: send:".format(self._host, self.port, self._skt.fileno()), e)
                        self.connect_close()
            else:
                if self.state == 3:
                    if do_close:
                        self.connect_close()

    def execute(self):
        # Call it in the main loop
        if self._host != self.host:
            self.end()
        
        if self._socket is None:
            if self.begin() is None:
                return

        if self._skt is None:
            if not self.accept():
                return

        self.receive()

        if self._skt is None:
            return

        eol_pos = self._in_buf.find(b"\r\n\r\n")
        if eol_pos >= 0:
            request = self._in_buf[:eol_pos]
            self._in_buf = self._in_buf[eol_pos + 4:]
            route, arg = self.find_route(request)
            # print('route, arg', route, arg, request)
            # print('request', request)
            if route:
                route(self, arg, self.cargo)
                self.state = 3
            else:
                self.not_found()

        self.send(True)

    def add_route(self, path, handler, method="GET"):
        # Add new route 
        self._routes.update({path.encode() + b'\x00' + method.encode(): handler})

    def connection_send(self, buf):
        self._out_buf += buf
        self.send(False)

    status_message = {
        200: "OK",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        500: "Internal Server Error",
        }

    def out(self, response, status=200, content_type="Content-Type: text/html", extra_headers=None):
        # Send response to client
        '''
        ### speed optimized 
        self.connection_send("HTTP/1.0 {:d} {:s}\r\n{:s}\r\n".format(status, self.status_message[status], content_type))
        if extra_headers is not None:
            for header in extra_headers:
                self.connection_send("{:s}\r\n".format(header))
        self.connection_send("Cache-Control: no-store\r\n\r\n{:s}".format(response))  # + end of HTTP header
        '''
        ### memory optimized
        self.connection_send("HTTP/1.0 {:d} {:s}\r\n".format(status, self.status_message[status]))
        self.connection_send("{:s}\r\n".format(content_type))
        if extra_headers is not None:
            for header in extra_headers:
                self.connection_send("{:s}\r\n".format(header))
        self.connection_send("Connection: close\r\nCache-Control: no-store\r\n\r\n")
        self.connection_send(response)

    def not_found(self):
        # Not found action
        self.out("404", status=404, content_type="Content-Type: text/plain")

    def internal_error(self, error):
        # Catch error action
        output = StringIO()
        #print_exception(error, output)
        str_error = output.getvalue()
        output.close()
        try:
            self.out("Error: " + str_error, status=500, content_type="Content-Type: text/plain")
        except:
            pass

    #def on_request(self, handler):
    #    # Set request handler
    #    self._on_request_handler = handler

    def execute_txt(self):
        # Call it in the main loop
        if self._host != self.host:
            self.end()
        
        if self._socket is None:
            if self.begin() is None:
                return

        if self._skt is None:
            if not self.accept():
                return

        if self._skt is None:
            return

        #if (time() - self._success_time) > HEARTBEAT:
        #    self._out_index = 0
        #    self._out_buf = b'HEARTBEAT\n'
        #    self.send(False)

        self.receive()

        if self._skt is None:
            return

        eol_pos = self._in_buf.find(b"\n")
        if eol_pos >= 0:
            request = self._in_buf[:eol_pos]
            self._in_buf = self._in_buf[eol_pos + 1:]
            txt = self.find_route_txt(request)(self, self.cargo)
            self._out_buf += txt
            self.state = 3

        self.send(True)
