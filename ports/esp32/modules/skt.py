from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR  #, getaddrinfo

from sys import print_exception

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
        server_socket.settimeout(timeout)

        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Биндим сервер на нужный адрес и порт
        server_socket.bind((ip, port))

        # Установка максимального количество подключений
        server_socket.listen(backlog)

        #server_socket.settimeout(timeout)

        # Необходима обработка ошибок
        return server_socket
    except Exception as e:
        print("Error: open_server_socket():", e)
        print_exception(e)
        try:
            server_socket.close()
        except:
            pass
        return None

def close_socket(skt):
    if skt is not None:
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
            skt = None
            print("Socket closed: done")
        except Exception as e:
            print('close_socket():', e)
            #pass
    return skt
