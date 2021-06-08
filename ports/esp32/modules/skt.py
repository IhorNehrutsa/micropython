"""
Based on
MicroPyServer is a simple HTTP server for MicroPython projects.
@see https://github.com/troublegum/micropyserver
"""
from gc import collect
collect()
#from uerrno import EAGAIN
#collect()
#from io import StringIO
#collect()
#from sys import print_exception
#collect()
#from re import search, compile
#collect()
#from utime import ticks_diff, ticks_ms
#collect()
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR  #, getaddrinfo
collect()
#from network import WLAN, STA_IF, AP_IF, STAT_GOT_IP
#collect()

#from uri import URI_percent_decoding
#collect()
#import uselect as select
#import ujson as json
#import gc

# Говорит о том, сколько дескрипторов единовременно могут быть открыты
#_BACKLOG = 0  # ???
'''
socket.listen([backlog])
Enable a server to accept connections. If backlog is specified, it must be at least 0 (if it’s lower,
it will be set to 0); and specifies the number of unaccepted connections that the system will allow
before refusing new connections. If not specified, a default reasonable value is chosen.

Разрешить серверу принимать соединения. Если указано отставание , оно должно быть не менее 0 (если меньше,
будет установлено значение 0); и указывает количество неприемлемых подключений, которое система разрешит
до отказа от новых подключений. Если не указано, выбирается разумное значение по умолчанию.
'''

# #def open_client_socket(ip, port=0, address_family_type=socket.AF_INET, socket_type=socket.SOCK_STREAM, timeout=None, secure=False ):
# def _open_socket(ip, port=0, address_family_type=socket.AF_INET, socket_type=socket.SOCK_STREAM, timeout=None, secure=False):
#     if port == 0:
#         port = 8729 if secure else 8728
#
#     skt = None
#     addr_info = socket.getaddrinfo(ip, port, address_family_type, socket_type)
#     #print("addr_info", addr_info)
#     af, socktype, proto, canonname, sockaddr = addr_info[0]
#     try:
#         _skt = socket.socket(af, socktype, proto)
#     except OSError as e:
#         print("Error1: open_socket()", e.args[0], e)
#         _skt = None
#     if _skt is not None:
#         _skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         if secure:
#             try:
#                 import ussl as ssl
#             except ImportError:
#                 import ssl
#
#             skt = ssl.wrap_socket(_skt, ssl_version=ssl.PROTOCOL_TLSv1_2, ciphers="ADH-AES128-SHA256")
#             #skt = ssl.wrap_socket(_skt, ssl_version=ssl.PROTOCOL_TLS)
#             #skt = ssl.wrap_socket(_skt)
#         else:
#             skt = _skt
#
#         n = 5  # 5
#         while (n > 0) and (skt is not None):
#             try:
#                 skt.connect(sockaddr)
#                 break
#             except OSError as e:
#                 print("Error2: open_socket()", e.args[0], e)
#                 print("Try connecting to", sockaddr, "after a 1-second delay", n, "time(s)")
#                 try:
#                     skt.close()
#                     skt = None
#                 except:
#                     pass
#                 sleep_ms(1000)
#             n -= 1
#
#         if n == 0:
#             try:
#                 skt.close()
#             except:
#                 pass
#             skt = None
#
#     if skt is None:
#         print("Error: Could not open socket", sockaddr)
#     else:
#         print("Socket is opened", sockaddr)
#     return skt


def open_server_socket(ip, port=0, address_family_type=AF_INET, socket_type=SOCK_STREAM, timeout=0, backlog=0):
    try:
        # yapf: disable
        #         print("open_server_socket("
        #               'ip="{ip}", '
        #               "port={port}, "
        #               "address_family_type={address_family_type}, "
        #               "socket_type={socket_type}, "
        #               "backlog={backlog}, "
        #               "timeout={timeout}"
        #               ")".format(
        #             ip=ip,
        #             port=port,
        #             address_family_type=address_family_type,
        #             socket_type=socket_type,
        #             backlog=backlog,
        #             timeout=timeout
        #         ))
        # yapf: enable

        #for addr_info in getaddrinfo(ip, port, address_family_type, socket_type):
        #    print("addr_info", addr_info)

        # Создаем сокет, который работает без блокирования основного потока
        server_socket = socket(address_family_type, socket_type)

        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Биндим сервер на нужный адрес и порт
        server_socket.bind((ip, port))

        # Установка максимального количество подключений
        server_socket.listen(backlog)

        server_socket.settimeout(timeout)

        # Необходима обработка ошибок
        return server_socket
    except Exception as e:
        print("Error: open_server_socket():", e)
        #print_exception(e)
        try:
            server_socket.close()
        except:
            pass
        return None

def close_socket(skt):
    try:
        print("Socket close...", end=' ')
        print(skt, end=' ')
        print(skt.fileno(), end=' ')
    except:
        pass
    finally:
        print('')
    try:
        skt.close()
        print("Socket closed: done")
    except Exception as e:
        print('close_socket():', e)
        #pass
