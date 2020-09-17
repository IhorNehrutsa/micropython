"""
Based on
MicroPyServer is a simple HTTP server for MicroPython projects.
@see https://github.com/troublegum/micropyserver
"""

#import sys
#import gc
from re import search
from network import WLAN, STA_IF
import uerrno
import usocket as socket
#import uselect as select
#import ujson as json

from utime import ticks_diff
from utimes import times_ms

# Говорит о том, сколько дескрипторов единовременно могут быть открыты
MAX_CONNECTIONS = 1


def get_non_blocking_server_socket(server_ip, server_port, address_family_type=socket.AF_INET, socket_type=socket.SOCK_STREAM, max_connections=1):
    #for addr_info in socket.getaddrinfo(server_ip, server_port, address_family_type, socket_type):
    #    print("addr_info", addr_info)

    # Создаем сокет, который работает без блокирования основного потока
    server_socket = socket.socket(address_family_type, socket_type)
    server_socket.setblocking(False)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Биндим сервер на нужный адрес и порт
    server_socket.bind((server_ip, server_port))

    # Установка максимального количество подключений
    server_socket.listen(max_connections)

    # Необходима обработка ошибок
    return server_socket


class MicroPyServer(object):
    def __init__(self, host="localhost", port=80):
        """ Constructor """
        if host in ("localhost", "127.0.0.1", "127.0.0.0/8", "0.0.0.0", ""):
            wlan = WLAN(STA_IF)
            if_config = wlan.ifconfig()
            # print(if_config)
            self._host = if_config[0]
        else:
            self._host = host
        self._port = port

        self._routes = []
        #self._on_request_handler = None

        self._socket = None
        self._connect = None
        self._client_address = None

        #self._poll = select.poll()

        self._request = None
        self._arg = ""

        # Откуда и куда записывать информацию
        #self.INPUTS = []  # list()
        #self.OUTPUTS = []  # list()
        #self.REQUEST = []

    def __del__(self):
        """ Destructor """  # Special method __del__ not implemented for user-defined classes in MicroPython !!!
        #print("Destructor", self)  # self.__class__.__name__,
        self.end()

    def find_route(self, request):
        """ Find route """
        # print("request ->", request, "<- request")
        lines = request.split("\r\n")
        #print("lines ->", lines[0], "<- lines")
        method = search("^([A-Z]+)", lines[0]).group(1)
        #print("method ->", method, "<- method")
        path_ = search("^[A-Z]+\\s+(/[-a-zA-Z0-9_.]*)", lines[0])
        #print("path ->", type(path_), "<- path")
        path = path_.group(1)
        #print("path ->", type(path), "<- path")
        #print("path ->", path, "<- path")
        #print("path ->", path_.start(), "<- path")
        #print("path ->", path_.end(1), "<- path")
        #print("path ->", path_.span(0), "<- path")
        arg = search("^[A-Z]+\\s+(/[-a-zA-Z0-9_.\?\=]*)", lines[0]).group(1)
        #print("arg ->", arg, "<- arg")

        self._arg = None
        if path == "/handler":
            self._arg = arg[arg.find("?") + 1:]
            #print("arg ->", self._arg, "<- arg")
        elif path == "/get":
            self._arg = arg[arg.find("?") + 1:]
            #print("arg ->", self._arg, "<- arg")

        for route in self._routes:
            if method != route["method"]:
                continue
            if path == route["path"]:
                return route
                #return (route, arg)
            else:
                match = search("^" + route["path"] + "$", path)
                if match:
                    # print(method, path, route["path"])
                    return route
                    #return (route, arg)
        return None

    def find_route_txt(self, path):
        """ Find route txt """
        for route in self._routes:
            if path == route["path"]:
                return route
        return None

    def begin(self):
        ''' Call it before the main loop '''
        print("Web MicroPyServer is starting at address %s:%d" % (self._host, self._port))
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self._host, self._port))

            self._socket.listen(MAX_CONNECTIONS)
            self._socket.setblocking(False)
        except:
            print("except begin")
            self.end()

    def end(self):
        #print("end(self)")
        if self._connect is not None:
            try:
                self._connect.close()
                #print("self._connect.close()")
            except:
                pass
            self._connect = None
        if self._socket is not None:
            try:
                self._socket.close()
                #print("self._socket.close()")
            except:
                pass
            self._socket = None

    def connect_close(self):
        try:
            #print(self._connect)
            self._connect.close()
            #print("connect_close(self)")
        except:
            pass
        self._connect = None

    def execute(self):
        ''' Call it in the main loop '''
        if not self._socket:
            self.begin()
        if not self._socket:
            return
        try:
            self._connect, self._client_address = self._socket.accept()
            self._connect.setblocking(False) # ???
            # self._connect.settimeout(5)
        except Exception as e:
            if e.args[0] != uerrno.EAGAIN:
                print("except : self._socket.accept():", e)
                raise
            return
        
        #print("do_recv 1")
        r = b""
        do_recv = True
        t = times_ms()
        while do_recv and (ticks_diff(times_ms(), t) < 50):
            try:
                rr = self._connect.recv(1024)
#                 print("===")
#                 print("rr", rr)
#                 print("===")
#                 print(str(rr, "utf8"))
#                 print("===")
                
                if rr == 0:
                    do_recv = False
                    print("web len(rr) == 0")
                    self._connect.close() # ???
                else:    
                    r += rr
                if rr.find(b"\r\n\r\n") >= 0:
#                    print('rr.find(b"\r\n\r\n")')
                    do_recv = False
            except Exception as e:
#                print("Exception as e: ooo", e.args[0], e)
                if (e.args[0] != uerrno.EAGAIN):
                    print("Exception as e: aaa", e.args[0], e)
                    do_recv = False
        #print("do_recv 2")

        if len(r) == 0:
            #print("web len(r) == 0")
            return

        try:
            #request = self.get_request()
            request = str(r, "utf8")

            #if self._on_request_handler:
            #    if not self._on_request_handler(request, address):
            #        pass

            #print("")
            #print(request)

            route = self.find_route(request)
            #print("web route:", route)
            if route:
                route["handler"](request, self._arg)
            else:
                self.not_found()

        except Exception as e:
            print(e.args[0], e)
            if (e.args[0] != uerrno.EAGAIN) and (e.args[0] != uerrno.ETIMEDOUT):
                print("Exception as e: bbb", e.args[0], e)
                self.internal_error(e)
                raise

    def start(self):
        """ Start server """
        self.begin()
        while True:
            self.execute()

    def add_route(self, path, handler, method="GET"):
        """ Add new route  """
        self._routes.append({"path": path, "handler": handler, "method": method})

    def out(self, response, status=200, content_type="Content-Type: text/plain", extra_headers=[]):
        """ Send response to client """
        if self._connect is None:
            raise Exception("Can not send response, no connection instance")

        status_message = {
            200: "OK",
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            }
        #sendall <-> write
        self._connect.write("HTTP/1.0 " + str(status) + " " + status_message[status] + "\r\n")
        #self._connect.write(b"HTTP/1.0 " + status.to_bytes(3, "big") + b" " + status_message[status] + b"\r\n")
        self._connect.write(content_type + "\r\n")
        #self._connect.write(content_type + b"\r\n")
        for header in extra_headers:
            self._connect.write(header + "\r\n")
        self._connect.write("X-Powered-By: MicroPyServer\r\n")
        self._connect.write("\r\n")
        self._connect.write(response)
        #self.end()

    def not_found(self):
        """ Not found action """
        self.out("404", status=404)

    def internal_error(self, error):
        """ Catch error action """
        '''
        output = io.StringIO()
        sys.print_exception(error, output)
        str_error = output.getvalue()
        output.close()
        '''
        try:
            self.out("Error: " + str_error, status=500)
        except:
            pass

    #def on_request(self, handler):
    #    """ Set request handler """
    #    self._on_request_handler = handler

    #def get_request(self):
    #    """ Return request body """
    #    return str(self._connect.recv(1024), "utf8")

    def execute_txt(self):
        ''' Call it in the main loop '''
        if self._socket is None:
            try:
                print("Txt MicroPyServer is starting at address %s:%d" % (self._host, self._port))
                self._socket = get_non_blocking_server_socket(self._host, self._port, max_connections=MAX_CONNECTIONS)
            except Exception as e:
                self._socket = None  # перестраховка
                print("Error: get_non_blocking_server_socket()", e.args[0], e)
                return

        if self._connect is None:
            try:
                self._connect, self._client_address = self._socket.accept()
                self._connect.settimeout(0)  # non blocking # ???
                #self._connect.settimeout(0.5) # TIMEDOUT
                #self._connect.settimeout(None) # blocking
                #print("self._connect, self._client_address", self._connect, self._client_address)
            except Exception as e:
                self._connect = None  # перестраховка
                if e.args[0] == uerrno.EAGAIN:
                    return
                print("Error: socket.accept()", e.args[0], e)
                self.connect_close()
                #raise
                return
        if self._connect is None:
            return

        #print("22")
        #t_ = times_ms()
        try:
            # r = readWord(self._connect)
            r = self._connect.recv(1024)
            if len(r) == 0:
                print("txt len(r)==0")
                self.connect_close()
                return
        except Exception as e:
            if e.args[0] in (uerrno.EAGAIN, uerrno.ETIMEDOUT):  # , uerrno.ECONNRESET
                return
            print("Error: receive", e.args[0], e)
            self.connect_close()
            #raise
            return

        #t = times_ms()
        #if (t - t_ > 10):
        #    print("txt connect.recv(), ms", t - t_)

        #print("33")
        request = str(r, "utf8")
        #print(request)
        route = self.find_route_txt(request)
        #print("txt route:", route)
        if route is None:
            print("Error: txt route not found", request)
            #self.not_found()
            return
        txt = route["handler"](request, self._arg, self._connect)
        len_txt = len(txt)
        if len_txt == 0:
            return
        #t_ = times_ms()
        try:
            n = 0
            while n < len_txt:
                r = self._connect.send(txt[n:])
                n += r
                if r == 0:
                    print("txt r==0")
                    self.connect_close()
                    return

        except Exception as e:
            if e.args[0] in (uerrno.EAGAIN, uerrno.ETIMEDOUT):  # , uerrno.ECONNRESET
                return

            print("Error: send", e.args[0], e)
            self.connect_close()
            #raise
            return

        #t = times_ms()
        #if (t - t_ > 10):
        #    print("txt connect.send(), ms", t - t_)
