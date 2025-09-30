USE_ROUTEROS_API = 1

from gc import collect, mem_free
from sys import print_exception
from ujson import dumps, loads
from network import WLAN, AP_IF, STA_IF
import WiFi

from saves import *

import power

try:
    import config
except ImportError:
    pass

try:
    import config_offset
except ImportError:
    pass

try:
    import config_search
except ImportError:
    pass

try:
    import config_WiFi
except ImportError:
    pass

file = open("index.html")
html = file.read()
file.close()
pos1 = html.find("<form action=")
html1 = html[:pos1]
pos2 = html.find("</form>")
html2 = html[pos1:pos2]
html = html[pos2:]

file = open("config.html")
html_config = file.read()
file.close()

file = open("config_WiFi.html")
html_config_WiFi = file.read()
file.close()

file = open("config_speed.html")
html_config_speed = file.read()
file.close()

file = open("debug.html")
html_debug = file.read()
file.close()


def show_index_page(server, arg, owl):
    if WiFi.wlan_ap.active():
        show_config_WiFi_page(server, arg, owl)
        return

    if arg == "/?":
        owl.autorefresh = False
    elif arg == "/?autorefresh=on":
        owl.autorefresh = True

    #owl.s1 = "Roll:{:8.1f} Pitch:{:8.1f} Yaw:{:8.1f} PoE:{:.1f}V Batt:{:.1f}V Temp:{:.1f}C".format(owl.sensors.roll, owl.sensors.pitch, owl.sensors.yaw, power.V_PoE, power.V_BAT, power.esp32_Celsius)
    s1 = ""
    if owl.autorefresh:
        s1 = '<meta http-equiv="Refresh" content="2" />'
    _bst = str(owl.ros_best.values())
    bst = _bst[_bst.find('['):_bst.find(']') + 1]
    s2 = f"СРШ: {owl.value_now} {bst}" 
    s3 =    f"Азимут,°: {owl.azim.mover.angle_now} → {owl.azim.angle_target} ({owl.azim.min_search}, {owl.azim.max_search}) [{owl.azim.angle_best}]"
    s4 = f"Кут місця,°: {owl.elev.mover.angle_now} → {owl.elev.angle_target} ({owl.elev.min_search}, {owl.elev.max_search}) [{owl.elev.angle_best}]"

    input_a = str(owl.input_azim)
    input_e = str(owl.input_elev)

    checked0 = ""
    checked1 = ""
    checked2 = ""
    checked3 = ""
    checked4 = ""
    checked5 = ""
    checked6 = ""
    checked7 = ""
    checked8 = ""
    if owl.mode == owl.MD_OFF:
        checked0 = "checked"  # Нерухомо 0
    elif owl.mode == owl.MD_MANUAL:
        checked1 = "checked"  # Ручний 1
    elif owl.mode in (owl.MD_SECTOR_A, owl.MD_SECTOR_E):
        checked2 = "checked"  # Огляд границь 2 3
    elif owl.mode in (owl.MD_ESCORT_A, owl.MD_ESCORT_E):
        checked3 = "checked"  # Стеження хрестове 6 7
    elif owl.mode == owl.MD_SEARCH_A:
        checked4 = "checked"  # Пошук "Азимут" 4
    elif owl.mode == owl.MD_SEARCH_E:
        checked5 = "checked"  # Пошук "Кут місця" 5
    elif owl.mode == owl.MD_CIRCLE:
        checked8 = "checked"  # Стеження кругове 8

    collect()

    server.out("")
    collect()

    s = html1.format(s1, owl.SSID, s2, s3, s4)
    collect()
    server.connection_send(s)
    collect()

    s = html2.format(checked0, checked1, checked2, checked3, checked4, checked5, checked6, checked7, checked8)
    collect()
    server.connection_send(s)
    collect()

    checked9 = ""
    if owl.autorefresh:
        checked9 = "checked"
    s = html.format(input_a, input_e, checked9)
    collect()
    server.connection_send(s)
    server.connection_send("\n")
    collect()
    #print(s)


def show_config_page(server, arg, owl):
    collect()
    s1 = "СРШ: " + dumps(owl.value_now)
    s = html_config.format(
        s1,  #
        owl.ROUTEROS_IP,  #
        owl.ROUTEROS_USER,  #
        owl.ROUTEROS_PASSWORD,  #
        owl.RADIO_NAME
        )
    collect()
    server.out(s)


def show_config_WiFi_page(server, arg, owl):
    collect()
    s1 = "СРШ: " + owl.ROUTEROS_IP + '<br>' + str(WiFi.WiFi_info()) +'<br>' + str(WiFi.ssid_list)
    s = html_config_WiFi.format(
        s1,  #
        WiFi.SSID,  #
        WiFi.PASSWORD,  #
        WiFi.OWL_IP,  #
        WiFi.OWL_SUBNET,  #
        WiFi.OWL_GATEWAY,  #
        WiFi.OWL_DNS
        )
    collect()
    server.out(s)


def show_config_speed_page(server, arg, owl):
    collect()
    s = html_config_speed.format(
        str(owl.azim.mover.accel.angle_accel_decel),  #
        str(round(owl.azim.mover.rpm_high, 2)),  #
        str(round(owl.azim.mover.rpm_low, 2)),  #
        str(owl.elev.mover.accel.angle_accel_decel),  #
        str(round(owl.elev.mover.rpm_high, 2)),  #
        str(round(owl.elev.mover.rpm_low, 2))
        )
    collect()
    server.out(s)


def show_debug_page(server, arg, owl):
    collect()
    try:
        try:
            #print(f'eval() Expression:>{owl.expression}< {type(owl.expression)}')
            eval_owl_expression = eval(owl.expression)
            #print(f'eval() eval_owl_expression:>{eval_owl_expression}< {type(eval_owl_expression)}')
        except SyntaxError as e:
            #print(f'exec() Expression:>{owl.expression}< {type(owl.expression)}')
            exec(owl.expression)
            #print(f'exec() Ok')

            owl_expression = owl.expression
            #print(f'owl_expression = >{owl_expression}< {type(owl_expression)}')
            owl_expression = owl_expression[:owl_expression.find('=')]
            #print(f'owl_expression = >{owl_expression}< {type(owl_expression)}')

            eval_owl_expression = eval(owl_expression)
            #print(f'eval_owl_expression = >{eval_owl_expression}< {type(eval_owl_expression)}')

        debug_value = dumps(eval_owl_expression)
    except Exception as e:
        debug_value = 'Error:' + dumps(e)
    #print(f'Value:>{debug_value}< {type(debug_value)}')
    collect()
    owl.s1 = f"Roll:{owl.sensors.roll} Pitch:{owl.sensors.pitch} Yaw:{owl.sensors.yaw} PoE:{power.V_PoE()}V Batt:{power.V_BAT()}V Temp:{power.esp32_Celsius}|{owl.sensors.temperature}°C Mover:{owl.azim.mover.is_ready()} {owl.elev.mover.is_ready()} Mem:{mem_free()}"
    collect()
    s = html_debug.format(owl.s1, owl.expression, debug_value)
    collect()
    server.out(s)


#--------------------------------------------------------
def do_save_config(server, arg, owl):
    save_config(owl)
    show_config_page(server, arg, owl)


def do_save_config_speed(server, arg, owl):
    save_config_speed(owl)
    show_config_speed_page(server, arg, owl)


def do_connect_config_WiFi(server, arg, owl):
    # WiFi_login(config_WiFi.SSID, config_WiFi.PASSWORD, config_WiFi.OWL_IP, config_WiFi.OWL_SUBNET, config_WiFi.OWL_GATEWAY, config_WiFi.OWL_DNS)
    show_config_WiFi_page(server, arg, owl)
    WiFi.save_config_WiFi(WiFi.SSID, WiFi.PASSWORD, (WiFi.OWL_IP, WiFi.OWL_SUBNET, WiFi.OWL_GATEWAY, WiFi.OWL_DNS))
    WiFi.net_state = WiFi.NET_STA_INIT


def do_save_config_WiFi(server, arg, owl):
    if WiFi.wlan_sta.isconnected():
        WiFi.save_config_WiFi(WiFi.SSID, WiFi.PASSWORD, (WiFi.OWL_IP, WiFi.OWL_SUBNET, WiFi.OWL_GATEWAY, WiFi.OWL_DNS))
    show_config_WiFi_page(server, arg, owl)


#--------------------------------------------------------
def do_handler(server, arg, owl):
    try:
        owl.mode = int(arg[-1:])
        #print('owl.mode=', owl.mode, 'arg=', arg)
        if owl.mode > owl.MD_MANUAL:
            owl.autorefresh = False
        show_index_page(server, arg, owl)
        owl.auto_start = False
    except Exception as e:
        print_exception(e)
        pass


def SET0(owl):
    owl.azim.mover.set0()
    owl.elev.mover.set0()
    save_config_offset(owl)

    owl.ros_best = {}
    owl.azim.angle_best = None
    owl.elev.angle_best = None


def do_SET0(server, arg, owl):
    SET0(owl)
    show_index_page(server, arg, owl)


#--------------------------------------------------------
def get_arg(arg_str):
    _from = arg_str.find("=") + 1
    _to = arg_str.find("&")
    if _to > _from:
        s = arg_str[_from:_to]
    else:
        s = arg_str[_from:]
    return s

def arg2val(arg):
    val = None
    s = get_arg(arg)

    if s == '':
        val = ''
    else:        
        try:
            val = loads(s)
        except ValueError as e:
            #print('C arg=', arg, 's=', s, 'val=', val,'Error:', e)
            try:
                val = eval(s)
            except SyntaxError as e:
                #print('B arg=', arg, 's=', s, 'val=', val,'Error:', e)
                if s.count('.') == 3: # net adress or mask
                    val = s
            except Exception as e:
                #print('C arg=', arg, 's=', s, 'val=', val,'Error:', e)
                val = s
    #print(f'arg=>{arg}< s=>{s}< val=>{val}< type(val)={type(val)}')
    return val, s


def do_get(server, arg, owl):
    val, s = arg2val(arg)
    if val is not None:
        if arg.find("input_a=") > 0:
            owl.input_azim = val
            if arg.find("&max=") > 0:
                if val <= owl.azim.mover.angle_max_limit:
                    if val > owl.azim.min_search:
                        owl.azim.max_search = val
                        save_config_search(owl)
            elif arg.find("&min=") > 0:
                if val >= owl.azim.mover.angle_min_limit:
                    if val < owl.azim.max_search:
                        owl.azim.min_search = val
                        save_config_search(owl)
            else:
                owl.azim.angle_target = val
        elif arg.find("input_e=") > 0:
            owl.input_elev = val
            if arg.find("&max=") > 0:
                if val <= owl.elev.mover.angle_max_limit:
                    if val > owl.elev.min_search:
                        owl.elev.max_search = val
                        save_config_search(owl)
            elif arg.find("&min=") > 0:
                if val >= owl.elev.mover.angle_min_limit:
                    if val < owl.elev.max_search:
                        owl.elev.min_search = val
                        save_config_search(owl)
            else:
                owl.elev.angle_target = val
    show_index_page(server, arg, owl)
    owl.auto_start = False


def do_get_config(server, arg, owl):
    if USE_ROUTEROS_API:
        val, s = arg2val(arg)
        if val is not None:
            if arg.find("ROUTEROS_IP=") >= 0:
                if val.count('.') == 3:
                    if owl.ROUTEROS_IP != val:
                        owl.ROUTEROS_IP = val
            elif arg.find("ROUTEROS_USER=") >= 0:
                if owl.ROUTEROS_USER != val:
                    owl.ROUTEROS_USER = val
            elif arg.find("PASSWORD=") >= 0:
                if owl.ROUTEROS_PASSWORD != s:
                    owl.ROUTEROS_PASSWORD = s
            elif arg.find("radio_name=") >= 0:
                owl.RADIO_NAME = val
                owl.RADIO_NAME = val
                if owl.ros_api:
                    owl.ros_api.radio_name = b"=radio-name=" + owl.RADIO_NAME
            owl.deinit_ros_api()
            owl.init_ros_api(owl.ROUTEROS_USER, owl.ROUTEROS_PASSWORD, owl.ROUTEROS_IP)
#             owl.deinit_ros_api2()
#             owl.init_ros_api2(owl.ROUTEROS_USER, owl.ROUTEROS_PASSWORD, owl.ROUTEROS_IP)
    show_config_page(server, arg, owl)


def do_get_config_WiFi(server, arg, owl):
    val, s = arg2val(arg)
    #print('val, arg', val, arg)
    if val is not None:
        if arg.find("SSID=") >= 0:
            #if val in WiFi.ssid_list:
            WiFi.SSID = val
        elif arg.find("PASSWORD=") >= 0:
            WiFi.PASSWORD = val
        elif arg.find("OWL_IP=") >= 0:
            val = val.lower()
            if val.count('.') == 3 or val == 'dhcp':
                WiFi.OWL_IP = val
                if val.count('.') == 3:
                    WiFi.OWL_GATEWAY = val[:val.rfind('.')] + '.1'
                    WiFi.OWL_DNS = WiFi.OWL_GATEWAY
        elif arg.find("OWL_SUBNET=") >= 0:
            if val.count('.') == 3:
                WiFi.OWL_SUBNET = val
        elif arg.find("OWL_GATEWAY=") >= 0:
            if val.count('.') == 3:
                WiFi.OWL_GATEWAY = val
                if val.count('.') == 3:
                    WiFi.OWL_DNS = WiFi.OWL_GATEWAY
        elif arg.find("OWL_DNS=") >= 0:
            if val.count('.') == 3:
                WiFi.OWL_DNS = val
        else:
            raise OwlError
    show_config_WiFi_page(server, arg, owl)


def do_get_config_speed(server, arg, owl):
    val, s = arg2val(arg)
    if val is not None:
        if arg.find("azim_angle_accel_decel=") > 0:
            owl.azim.mover.accel.angle_accel_decel = val
        elif arg.find("azim_rpm_low=") > 0:
            owl.azim.mover.rpm_low = val
        elif arg.find("azim_rpm_high=") > 0:
            owl.azim.mover.rpm_high = val

        elif arg.find("elev_angle_accel_decel=") > 0:
            owl.elev.mover.accel.angle_accel_decel = val
        elif arg.find("elev_rpm_low=") > 0:
            owl.elev.mover.rpm_low = val
        elif arg.find("elev_rpm_high=") > 0:
            owl.elev.mover.rpm_high = val
    show_config_speed_page(server, arg, owl)


def do_get_debug(server, arg, owl):
    s = get_arg(arg)
    if arg.find("expression=") > 0:
        owl.expression = s
    show_debug_page(server, arg, owl)


#--------------------------------------------------------
def do_CW(server, arg, owl):
    owl.azim.angle_target = round(owl.azim.angle_target + 1, 1)
    show_index_page(server, arg, owl)
    owl.auto_start = False


def do_CCW(server, arg, owl):
    owl.azim.angle_target = round(owl.azim.angle_target - 1, 1)
    show_index_page(server, arg, owl)
    owl.auto_start = False


def do_UP(server, arg, owl):
    owl.elev.angle_target = round(owl.elev.angle_target + 1, 1)
    show_index_page(server, arg, owl)
    owl.auto_start = False


def do_DOWN(server, arg, owl):
    owl.elev.angle_target = round(owl.elev.angle_target - 1, 1)
    show_index_page(server, arg, owl)
    owl.auto_start = False


def park(server, arg, owl):
    print("Park")
    owl.azim.angle_target = 0
    owl.elev.angle_target = 0
    owl.mode = owl.MD_MANUAL
    show_index_page(server, arg, owl)
