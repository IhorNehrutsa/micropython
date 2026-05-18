import uasyncio as asyncio
import binascii
import hashlib
from sys import print_exception
from gc import collect

# Спроба імпорту ssl для захищених з'єднань
try:
    import ussl as ssl
except ImportError:
    import ssl

class ApiRos:
    "RouterOS API - Asynchronous version for MicroPython"
    
    def __init__(self, reader, writer, timeout=5):
        self.reader = reader
        self.writer = writer
        self.timeout = timeout
        self.state = 1 # READY
        self.value = None
        
    async def close(self):
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass
        finally:
            self.state = 6 # LOST

    async def login(self, username, pwd):
        try:
            # Перший крок логіну для отримання челенджу
            replies = await self.talk(["/login", "=name=" + username, "=password=" + pwd])
            
            for repl, attrs in replies:
                if repl == "!trap":
                    return False
                elif "=ret" in attrs:
                    # Хешування челенджу (старий метод API)
                    chal = binascii.unhexlify(attrs["=ret"].encode())
                    md = hashlib.md5()
                    md.update(b"\x00")
                    md.update(pwd.encode())
                    md.update(chal)
                    
                    response = "00" + binascii.hexlify(md.digest()).decode()
                    replies2 = await self.talk([
                        "/login", 
                        "=name=" + username, 
                        "=response=" + response
                    ])
                    
                    for repl2, attrs2 in replies2:
                        if repl2 == "!trap":
                            return False
            
            print("RouterOS logged in:", username)
            return True
        except Exception as e:
            print("Login error:", e)
            return False

    async def talk(self, words):
        if not words:
            return []
        
        await self.write_sentence(words)
        
        responses = []
        while True:
            sentence = await self.read_sentence()
            if not sentence:
                continue
                
            reply = sentence[0]
            attrs = {}
            for w in sentence[1:]:
                j = w.find("=", 1)
                if j == -1:
                    attrs[w] = ""
                else:
                    attrs[w[:j]] = w[j + 1:]
            
            responses.append((reply, attrs))
            if reply == "!done":
                return responses

    async def write_sentence(self, words):
        for w in words:
            await self.write_word(w)
        await self.write_word("") # End of sentence
        await self.writer.drain()

    async def write_word(self, word):
        b_word = word.encode('utf-8')
        await self.write_len(len(b_word))
        self.writer.write(b_word)

    async def write_len(self, length):
        if length < 0x80:
            self.writer.write(length.to_bytes(1, 'big'))
        elif length < 0x4000:
            length |= 0x8000
            self.writer.write(length.to_bytes(2, 'big'))
        elif length < 0x200000:
            length |= 0xC00000
            self.writer.write(length.to_bytes(3, 'big'))
        elif length < 0x10000000:
            length |= 0xE0000000
            self.writer.write(length.to_bytes(4, 'big'))
        else:
            self.writer.write(b'\xf0')
            self.writer.write(length.to_bytes(4, 'big'))
            
    async def reader_readexactly(self, length):
        return await asyncio.wait_for(self.reader.readexactly(length), timeout=self.timeout)            

    async def read_sentence(self):
        sentence = []
        while True:
            length = await self.read_len()
            if length == 0:
                return sentence
            
            data = await self.reader_readexactly(length)
            sentence.append(data.decode('utf-8', 'replace'))

    async def read_len(self):
        # Читаємо перший байт довжини
        c = (await self.reader_readexactly(1))[0]
        
        if (c & 0x80) == 0x00:
            return c
        elif (c & 0xC0) == 0x80:
            c &= ~0xC0
            return (c << 8) + (await self.reader_readexactly(1))[0]
        elif (c & 0xE0) == 0xC0:
            c &= ~0xE0
            data = await self.reader_readexactly(2)
            return (c << 16) + (data[0] << 8) + data[1]
        elif (c & 0xF0) == 0xE0:
            c &= ~0xF0
            data = await self.reader_readexactly(3)
            return (c << 24) + (data[0] << 16) + (data[1] << 8) + data[2]
        elif (c & 0xF8) == 0xF0:
            data = await self.reader_readexactly(4)
            return (data[0] << 24) + (data[1] << 16) + (data[2] << 8) + data[3]
        return 0

    async def _read_sentence_as_bytes(self):
        """Допоміжний метод для читання сирих байтів одного речення"""
        sentence = b""
        while True:
            length = await self.read_len()
            if length == 0:
                return sentence + b"\x00" # Додаємо термінатор для зручності пошуку
            
            word = await self.reader_readexactly(length)
            sentence += word + b"\x00"
        return sentence

    async def execute_and_get_params(self, command, radio_name, params):
        """
        Відправляє команду та чекає на специфічні параметри, 
        використовуючи пряме очікування відповіді.
        """
        collect()
        self.command = command
        self.radio_name = radio_name
        self.params = params
    
        try:
            # 1. Відправка команди
            await self.write_sentence([self.command])
            
            # 2. Пряме читання відповідей до моменту !done
            full_data = b""
            while True:
                # Читаємо одне речення (sentence) з API
                sentence_bytes = await self._read_sentence_as_bytes()
                
                # Якщо це кінець транзакції
                if b"!done" in sentence_bytes:
                    break
                
                # Накопичуємо дані для пошуку (тільки якщо це репліка з даними)
                if b"!re" in sentence_bytes or b"!trap" in sentence_bytes:
                    full_data += sentence_bytes
            
            return self._parse_parameters(full_data)

        except Exception as e:
            print(f"Error during command execution: {e}")
            await self.close()
            return None

    def _parse_parameters(self, data):
        if not data:
            return {}
    
        #print('full_data:', data)
        
        radio_name_b = self.radio_name.encode() if isinstance(self.radio_name, str) else self.radio_name
        index_radio = data.find(b'=' + radio_name_b + b'\x00')

        if index_radio == -1:
            return {}
    
        results = {}
        # Створюємо memoryview один раз для ефективного витягування значень
        mv = memoryview(data)
        data_len = len(data)

        for param in self.params:
            param_b = param.encode() if isinstance(param, str) else param
            search_key = b'=' + param_b + b'='

            # Шукаємо в об'єкті bytes (data)
            start_idx = data.find(search_key, index_radio)
            
            if start_idx != -1:
                val_start = start_idx + len(search_key)
                # Шукаємо кінець значення (нульовий байт)
                val_end = data.find(b'\x00', val_start)
                
                if val_end != -1:
                    try:
                        # Спроба 1: Пряме перетворення в int (якщо там чисте число)
                        # Спроба прямого перетворення (найшвидша)
                        results[param] = int(mv[val_start:val_end])
                    except (ValueError, SyntaxError) as e:
                        # print_exception(e)
                        try:
                            # Спроба 2: Через float (ігнорує пробіли та специфічні закінчення)
                            # Отримуємо значення. float() у MicroPython досить швидкий 
                            # і сам ігнорує зайві нечислові символи в кінці рядка,
                            # тому замість циклу просто перетворюємо зріз.
                            # Якщо в значенні можуть бути одиниці виміру (наприклад "120Mbps"),
                            # float() викличе помилку
                            results[param] = int(float(mv[val_start:val_end]))
                        except (ValueError, SyntaxError) as e:
                            # print_exception(e)
                            # Спроба 3: Ручна чистка від одиниць виміру (dBm, Mbps тощо)
                            # Якщо не просто число (наприклад, "-65dBm" або "54Mbps")
                            # Витягуємо тільки число (обробка від'ємних значень та цифр)
                            num_bytes = 0
                            # Безпечний цикл пошуку числової частини
                            while val_start + num_bytes < data_len:
                                char_code = mv[val_start + num_bytes]
                                # Дозволяємо: цифри, точку, мінус
                                # ASCII: 45='-', 46='.', 48-57='0-9' (виключаємо 47='/')
                                if 45 <= char_code <= 57 and char_code != 47:
                                    num_bytes += 1
                                else:
                                    break
                            #print('num_bytes:', num_bytes, data[val_start:val_start + num_bytes])
                            if num_bytes:
                                try:
                                    # Використовуємо float для обробки крапок, потім в int
                                    results[param] = int(float(mv[val_start:val_start + num_bytes])) 
                                except Exception as e:
                                    print_exception(e)
                        except Exception as e:
                            print_exception(e)
                    except Exception as e:
                        print_exception(e)
                        continue
        
        self.value = results
        return results

    async def handle_command(self):
        #print(self.command, self.radio_name, self.params)
        await self.execute_and_get_params(self.command, self.radio_name, self.params)
        #print('handle_command:', self.value)
        return

# --- Функція для підключення ---
async def connect_ros(ip, port=None, username="admin", password="", secure=False):
    if port is None:
        port = 8729 if secure else 8728
        
    print(f"Connecting to RouterOS {ip}:{port}...")
    try:
        reader, writer = await asyncio.open_connection(ip, port)
        
        if secure:
            # MicroPython SSL wrap (може вимагати багато RAM)
            import ussl
            # Примітка: SSL в asyncio MicroPython може бути складним 
            # залежить від конкретної прошивки
            print("SSL warning: ensure your firmware supports async SSL")

        api = ApiRos(reader, writer)
        if await api.login(username, password):
            return api
        else:
            await api.close()
            return None
    except Exception as e:
        print("Connection failed:", e)
        return None

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
