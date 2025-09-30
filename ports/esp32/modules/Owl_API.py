USE_ROUTEROS_API = 1
ROS_TIMEOUT = 1  # 0.1  # time in seconds
#OWL_TIMEOUT = 1

#ros_command = ["/interface/wireless/align/print"]
#ros_command = ["/interface/wireless/align/monitor/wlan1"]  #
ros_command = "/interface/wireless/registration-table/print"

ros_params = (b"=signal-strength=", b"=signal-to-noise=")
#ros_params = (b"=signal-strength-ch0=", b"=signal-to-noise=")

from gc import collect

from utime import ticks_ms, ticks_diff
from machine import unique_id

#import config_version
from RouterOS_API import open_socket, ApiRos

from avg_filter import *

from diagram import *

#from coord import *
#from step_motor_pid import *

t_ROS = 0


class OwlError(Exception):
    pass


def value_sub(value1, value2, ros_params):
    if (len(value1) > 0) and (len(value2) == 0):
        return 1
    if (len(value1) == 0) and (len(value2) > 0):
        return -1
    res = 0
    if (len(value1) > 0) and (len(value2) > 0):
        for ros_param in ros_params:
            sub = value1[ros_param] - value2[ros_param]
            if sub > 0:
                if sub > res:
                    res = sub
            else:
                if sub < res:
                    res = sub
    return res


def value_cmp(value1, value2, ros_params):
    if (len(value1) > 0) and (len(value2) == 0):
        return 1
    if (len(value1) == 0) and (len(value2) > 0):
        return -1
    res = 0
    if (len(value1) > 0) and (len(value2) > 0):
        for ros_param in ros_params:
            if value1[ros_param] > value2[ros_param]:
                res += 1
            elif value1[ros_param] < value2[ros_param]:
                res -= 1
    return res


__t_ROS = ticks_ms()
_t_ROS = ticks_ms()


def handle_ros_command(owl):
    global _t_ROS, __t_ROS

    t_ROS = ticks_ms()

    owl_value_now = owl.value_now

#     azim_angle_now = owl.azim.mover.angle_now  # 1
#     elev_angle_now = owl.elev.mover.angle_now  # 1

    owl.value_now = None

    if owl.ros_api != None:
        if owl.ros_api.skt == None:
            owl.ros_api = None
            return
        owl.ros_api.handle_command()  # 2
        owl.value_now = owl.ros_api.value  # 3

    azim_angle_now = owl.azim.mover.angle_now  # 4
    elev_angle_now = owl.elev.mover.angle_now  # 4

    #owl.azim_angle_now = (azim_angle_now + owl.azim.mover.angle_now) / 2  # 4
    #owl.elev_angle_now = (elev_angle_now + owl.elev.mover.angle_now) / 2  # 4

    owl.azim_angle_now = round(azim_angle_now, 2)  # 5
    owl.elev_angle_now = round(elev_angle_now, 2)  # 5

    if owl.value_now is not None:
        if len(owl.value_now) > 0:
            if value_cmp(owl.value_now, owl.ros_best, ros_params) > 0:
                owl.ros_best = owl.value_now  # нашли "лучше" уровень сигнала
                owl.azim.angle_best = owl.azim_angle_now  # в этой позиции
                owl.elev.angle_best = owl.elev_angle_now  # в этой позиции

    if (owl.value_now == None) or (len(owl.value_now) == 0):
        if (owl_value_now != None) and (len(owl_value_now) != 0):
            owl.lost_timestamp = ticks_ms()
        owl.lost += 1
    else:
        owl.lost = 0
        owl.lost_timestamp = None

    if ticks_diff(ticks_ms(), __t_ROS) > 1000:
        __t_ROS = ticks_ms()
        #print('период опроса СРШ, мс', ticks_diff(t_ROS, _t_ROS), 'длительность опроса СРШ, мс', ticks_diff(ticks_ms(), t_ROS))
    _t_ROS = t_ROS


def print_motor(owl, motor, a, v):
    print("start", motor.angle_start, motor.value_start)  #, motor.avg_start)
    #print("plus_", motor.angle_plus, motor.value_plus)
    #print("minus", motor.angle_minus, motor.value_minus)
    print("best_", motor.angle_best, owl.ros_best)  #, motor.avg_best)
    #print("diff_", motor.angle_bisector_diff, motor.avg_bisector_diff)
    #print("max__", motor.angle_bisector_max, motor.avg_bisector_max)
    a = round(motor.angle_target, 1)
    b = round(motor.angle_start, 1)
    angle_now = round(motor.mover.angle_now, 1)
    if a != angle_now:
        print("end__", a, '<-', angle_now, v)

    if a > b:
        if owl.mode in (owl.MD_SECTOR_A, owl.MD_SEARCH_A, owl.MD_ESCORT_A):
            print('>>>')
        else:
            print('^^^')
    elif a < b:
        if owl.mode in (owl.MD_SECTOR_A, owl.MD_SEARCH_A, owl.MD_ESCORT_A):
            print('<<<')
        else:
            print('vvv')
    else:
        if owl.mode in (owl.MD_SECTOR_A, owl.MD_SEARCH_A, owl.MD_ESCORT_A):
            print('>|<')
        else:
            print('-X-')


def calc_angles(owl, motor):
    print("calc_angles()", motor.mover.name)
    #print(len(owl.angle_diagram[b"angle"]), owl.angle_diagram)
    #print(motor.mover.angle_now, motor.angle_target)
    if len(owl.angle_diagram[b"angle"]) > 0:
        #print(len(owl.angle_diagram[b"angle"]), owl.angle_diagram)

        owl.remove_same_values()
        owl.calc_diff_gradient()
        #print(len(owl.angle_diagram[b"angle"]), owl.angle_diagram)
        owl.remove_same_gradients()
        owl.calc_diff_gradient()

        owl.print_angle_diagram()

        owl.calc_indexes_and_angles(motor)
        return True
    return False


class Owl(object):
    ID = int.from_bytes(unique_id(), 'big')

    SSID = ''

    ROUTEROS_IP = ''
    ROUTEROS_USER = ''
    ROUTEROS_PASSWORD = ''
    RADIO_NAME = ''  # корреспондента

    LOSTS = 5

    ANTENNA_ANGLE = 1  # 5  # antenna beamwidth angle # угол луча антенны

    # motion modes
    MD_OFF = 0  # motion off
    MD_COMMUNICATE = 1  #
    MD_MANUAL = 2  # manual motion
    MD_SECTOR_A = 3  # azimuth
    MD_SECTOR_E = 4  # elevation
    MD_SEARCH_A = 5  # search azimuth
    MD_SEARCH_E = 6  # seach elevation
    MD_ESCORT_A = 7  # escort azimuth  # хрестовое слежение
    MD_ESCORT_E = 8  # escort elevation  # хрестовое слежение
    MD_CIRCLE = 9  # circle tracking  # круговое слежение
    '''
    0 - нет сигнала - поиск в секторе, снижаем/повышаем скорость раз в минуту несколько раз по 10% до 30%
    1 - увидел сигнал - останов, установление соединения
    2 - считывание состояния корреспондента
    3 - определение старшего по MAC
    4 - старший выполняет поиск в секторе, младший неподвижный
    5 - старший неподвижный, младший выполняет поиск в секторе
    6 - оба переходят в режим слежения
    7 - при отключении сигнала на 10 сек переходят в состояние 4
    '''
    # communication state
    CM_NO = 0
    CM_SEE = 1
    CM_READ = 2
    CM_DETECT = 3
    CM_SECTOR = 4
    CM_STAY = 5
    CM_ESCORT = 6

    def __init__(self, azim, elev, sensors, ros_params):
        self.sensors = sensors
        self.ros_api = None  # неблокирующий сокет для чтения SNR и Signal-strength
        self.ros_api2 = None  # блокирующий сокет для выполнения команд управления
        self.ros_command2 = None

        self.corr = None  # сова-корреспондент
        self.state = self.CM_NO
        self.сounter = 0  # счетчик поиска в секторе
        self.speed = 10
        self.speed_dir = -1
        self.sector_time = None

        self._mode = self.MD_MANUAL  # текущий режим
        self.mode_before = self.MD_MANUAL  # предыдущий режим, несовпадает с текущим всегда
        self.mode_prev = self.MD_MANUAL  # предыдущий режим, несовпадает с текущим один раз, служит для однократного срабатывания события при циклическом опросе

        self.auto_start = True

        self.ros_params = ros_params

        self.angle_diagram_init()
        self.filter_init()

        self.ros_best = {}  # лучшее значение в процессе поиска
        self.value_now = None
        self.azim_angle_now = 0
        self.elev_angle_now = 0

        #        self.roll = 0  # rotate around X
        #        self.pitch = 0  # rotate around Y
        #        self.yaw = 0  # rotate around Z

        self.lost = 0  # количество попыток перечитать уровень при утере сигнала
        self.lost_timestamp = None  # когда утеряли

        self.input_azim = 0  # поля для WEB интерфейса
        self.input_elev = 0  #

        self.expression = 'mem_free()'  # debug: request expression

        # motors ======================
        self.azim = azim
        self.elev = elev

        self.s1 = ''
        self.autorefresh = False

        self.ticks_ms = ticks_ms()

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, m):
        if self._mode != m:
            self.mode_before = self._mode  # 1
        self._mode = m  # 2

    # filter ----------------------------
    def filter_init(self):
        self.filter = {ros_param: MovingAverageFilter() for ros_param in self.ros_params}

    def filter_clear(self):
        for ros_param in self.ros_params:
            self.filter[ros_param].clear()

    def filter_is_full(self):
        return self.filter[self.ros_params[0]].is_full

    def filter_append(self, values):
        #if len(values) == len(self.ros_params):
        if len(values) > 0:
            for ros_param in self.ros_params:
                self.filter[ros_param].update(values[ros_param])

    def filter_avg(self):
        return {ros_param: self.filter[ros_param].average() for ros_param in self.ros_params}

    # diagram ----------------------------
    def angle_diagram_init(self):
        '''
        self.angle_diagram = {ros_param: {"value":[], # значения параметра 'ros_param' "value"[i] в позиции 'angle'[i]
                                          "diff":[], # разность значений ("value"[i+1] - "value"[i])
                                          "gradient":[], # напрвление изменения параметра 'ros_param': 0, -1, +1
                                          "max_value":0, # максимальное значения параметра 'ros_param'
                                          "mid_value":0, # значения параметра 'ros_param' в среднем направлении
                                          "mid_angle":0, # угол средний направления (искомый)
                                          "mid_angle2":0 # угол средний направления (искомый)
                                          } for ros_param in self.ros_params}
        '''
        self.angle_diagram = {ros_param: Diagram() for ros_param in self.ros_params}
        self.angle_diagram.setdefault(b"angle", [])
        #print(self.angle_diagram)
        #exit(0)

    def angle_diagram_clear(self):
        for ros_param in self.ros_params:
            self.angle_diagram[ros_param].clear()
        self.angle_diagram[b"angle"].clear()
        collect()
        #print(self.angle_diagram)
        #exit(0)

    def angle_diagram_append(self, angle, values):
        def app():
            self.angle_diagram[b"angle"].append(angle)
            for ros_param in self.ros_params:
                self.angle_diagram[ros_param].append(values[ros_param])

        #
        #if len(values) == len(self.ros_params):
        if len(values) > 0:
            if (self.len_angle_diagram() < 2):
                app()
                return
            val_2 = self.angle_diagram_value(self.len_angle_diagram() - 2)
            val_1 = self.angle_diagram_value(self.len_angle_diagram() - 1)
            a = self.angle_diagram[b"angle"][-1]
            if abs(a - angle) < 0.5:
                return
            if value_cmp(values, val_1, self.ros_params) != 0:
                app()
            else:  # values == val_1
                if value_cmp(val_1, val_2, self.ros_params) == 0:
                    #print('a', self.angle_diagram[b"angle"])
                    #print('a', self.angle_diagram[b"angle"][-1])
                    self.angle_diagram[b"angle"][-1] = angle
                else:
                    app()

    def angle_diagram_value(self, i):
        if (i < 0) or (i >= self.len_angle_diagram()):
            return {}
        return {ros_param: self.angle_diagram[ros_param].value[i] for ros_param in self.ros_params}

    def is_same_gradient(self):
        for i in range(len(self.angle_diagram[b"angle"]) - 3 - 1):  # - 1
            n = 0
            for ros_param in self.ros_params:
                if self.angle_diagram[ros_param].is_same_gradient(i):
                    n += 1
            if n == len(self.ros_params):
                return i + 1 + 1
        return -1

    def remove_same_gradients(self):
        i = self.is_same_gradient()
        while i >= 0:
            print(f"pop({i})")
            self.angle_diagram[b"angle"].pop(i)
            for ros_param in self.ros_params:
                self.angle_diagram[ros_param].pop(i)
            i = self.is_same_gradient()

    def len_angle_diagram(self):
        return len(self.angle_diagram[b"angle"])

    def count_same_values(self, i):
        count = 1
        val = self.angle_diagram_value(i)
        i -= 1
        while i >= 0:
            if value_cmp(val, self.angle_diagram_value(i), self.ros_params) == 0:
                count += 1
                i -= 1
            else:
                break
        return count

    def remove_same_values(self):
        i = self.len_angle_diagram() - 1
        while i > 1:
            n = self.count_same_values(i)
            while n > 2:
                self.angle_diagram[b"angle"].pop(i)
                for ros_param in self.ros_params:
                    self.angle_diagram[ros_param].value.pop(i)
                i -= 1
                n -= 1
            i -= 1

    def calc_diff_gradient(self):
        for ros_param in self.ros_params:
            self.angle_diagram[ros_param].calc_diff_gradient()

    def calc_indexes_and_angles(self, motor):
        motor.angle_bisector_diff = 0
        motor.angle_bisector_max = 0
        ok = True
        for ros_param in self.ros_params:
            self.angle_diagram[ros_param].calc_indexes()

            index_max_diff = self.angle_diagram[ros_param].index_max_diff
            if index_max_diff is None:
                ok = False
            else:
                index_min_diff = self.angle_diagram[ros_param].index_min_diff
                motor.angle_bisector_diff += self.angle_diagram[b"angle"][index_max_diff] + self.angle_diagram[b"angle"][index_min_diff]

                print("index_max_diff, index_min_diff", index_max_diff, index_min_diff)
                print("value[index_max_diff], value[index_min_diff]", self.angle_diagram[ros_param].value[index_max_diff], self.angle_diagram[ros_param].value[index_min_diff])
                print("diff[index_max_diff], diff[index_min_diff]", self.angle_diagram[ros_param].diff[index_max_diff], self.angle_diagram[ros_param].diff[index_min_diff])
                print("angle[index_max_diff], angle[index_min_diff]", self.angle_diagram[b"angle"][index_max_diff], self.angle_diagram[b"angle"][index_min_diff])

            index_right_max = self.angle_diagram[ros_param].index_right_max
            index_left_max = self.angle_diagram[ros_param].index_left_max
            motor.angle_bisector_max += self.angle_diagram[b"angle"][index_right_max] + self.angle_diagram[b"angle"][index_left_max]

            print("index_left_max, index_right_max", index_left_max, index_right_max)
            print("value[index_left_max], value[index_right_max]", self.angle_diagram[ros_param].value[index_left_max], self.angle_diagram[ros_param].value[index_right_max])
            print("angle[index_left_max], angle[index_right_max]", self.angle_diagram[b"angle"][index_left_max], self.angle_diagram[b"angle"][index_right_max])

        if ok:
            motor.angle_bisector_diff = round(motor.angle_bisector_diff / (2 * len(self.ros_params)), 1)
            #print("angle_bisector_diff", motor.angle_bisector_diff)
        else:
            motor.angle_bisector_diff = None

        motor.angle_bisector_max = round(motor.angle_bisector_max / (2 * len(self.ros_params)), 1)
        #print("angle_bisector_max", motor.angle_bisector_max)

    def print_angle_diagram(self):
        print("len=", len(self.angle_diagram[b"angle"]))
        print("angle=", self.angle_diagram[b"angle"])
        '''
        for ros_param in self.ros_params:
            print("value=", ros_param, self.angle_diagram[ros_param].value)
            print("diff=", ros_param, self.angle_diagram[ros_param].diff)
        '''

    def deinit_ros_api(self):
        if self.ros_api is not None:
            self.ros_api.close_socket()
            self.ros_api = None

    def init_ros_api(self, user="admin", passw="", ip="", port=8728, secure=False):
        if not USE_ROUTEROS_API:
            return None

        print(f"Try to open ROS socket {ip}:{port}")
        skt = open_socket(ip, port=port, secure=secure, timeout=ROS_TIMEOUT)
        if skt is None:
            print(f"Could not open ROS socket {ip}:{port}")
            return None

        ros_api = ApiRos(skt, timeout=ROS_TIMEOUT)

        if not ros_api.login(user, passw):
            print(f"Could not ROS login '{user}' to {ip}:{port}")
            return None

        ros_api.settimeout(0)  # time in seconds
        ros_api.command = ros_command
        ros_api.radio_name = b"=radio-name=" + self.RADIO_NAME
        ros_api.params = ros_params
        self.ros_api = ros_api
        return ros_api

    def deinit_ros_api2(self):
        if self.ros_api2 is not None:
            self.ros_api2.close_socket()
            self.ros_api2 = None

    def init_ros_api2(self, user="admin", passw="", ip="", port=0, secure=False):
        if not USE_ROUTEROS_API:
            return None

        print(f"Try to open ROS2 socket {ip}:{port}")
        skt = open_socket(ip, port=port, secure=secure, timeout=ROS_TIMEOUT)
        if skt is None:
            print(f"Could not open ROS2 socket {ip}:{port}")
            return None

        ros_api = ApiRos(skt, timeout=ROS_TIMEOUT)

        if not ros_api.login(user, passw):
            print(f"Could not ROS2 login '{user}' to {ip}:{port}")
            return None
        '''
        ros_api.settimeout(0)  #ROS_TIMEOUT)  #  1)#0.1)  # time in seconds
        ros_api.command = ros_command
        ros_api.radio_name = b"=radio-name=" + self.RADIO_NAME
        ros_api.params = ros_params
        '''
        self.ros_api2 = ros_api
        return ros_api
