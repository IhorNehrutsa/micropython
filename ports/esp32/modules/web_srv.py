USE_ROUTEROS_API = 1

from gc import collect, mem_free
from sys import print_exception
from ujson import dumps, loads
from network import WLAN, AP_IF, STA_IF
#import WiFi

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

def eval_debug_data(owl):
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

        result_value = dumps(eval_owl_expression)
    except Exception as e:
        result_value = 'Error:' + dumps(e)
    #print(f'Value:>{result_value}< {type(result_value)}')
    collect()
    data = {
        'debug_info': f"Roll:{owl.sensors.roll} Pitch:{owl.sensors.pitch} Yaw:{owl.sensors.yaw} PoE:{power.V_PoE()}V Batt:{power.V_BAT()}V Temp:{power.esp32_Celsius()}°C, {owl.sensors.temperature}°C Mover:{owl.azim.mover.is_ready()} {owl.elev.mover.is_ready()} Mem:{mem_free()}",
        'expression': owl.expression,
        'result_value': result_value
    }
    collect()
    return data
        
# #--------------------------------------------------------
# def do_save_config(server, arg, owl):
#     save_config(owl)
# 
# def do_save_config_speed(server, arg, owl):
#     save_config_speed(owl)
# 
# def do_connect_config_WiFi(server, arg, owl):
#     # WiFi_login(config_WiFi.SSID, config_WiFi.PASSWORD, config_WiFi.OWL_IP, config_WiFi.OWL_SUBNET, config_WiFi.OWL_GATEWAY, config_WiFi.OWL_DNS)
#     WiFi.save_config_WiFi(WiFi.SSID, WiFi.PASSWORD, (WiFi.OWL_IP, WiFi.OWL_SUBNET, WiFi.OWL_GATEWAY, WiFi.OWL_DNS))
#     WiFi.net_state = WiFi.NET_STA_INIT
# 
# 
# def do_save_config_WiFi(server, arg, owl):
#     if WiFi.wlan_sta.isconnected():
#         WiFi.save_config_WiFi(WiFi.SSID, WiFi.PASSWORD, (WiFi.OWL_IP, WiFi.OWL_SUBNET, WiFi.OWL_GATEWAY, WiFi.OWL_DNS))
# 
# 
# #--------------------------------------------------------
# def do_handler(server, arg, owl):
#     try:
#         owl.mode = int(arg[-1:])
#         #print('owl.mode=', owl.mode, 'arg=', arg)
#         owl.auto_start = False
#     except Exception as e:
#         print_exception(e)
#         pass


def set0(owl):
    owl.azim.mover.set0()
    owl.elev.mover.set0()
    save_config_offset(owl)

    owl.ros_best = {}
    owl.azim.angle_best = None
    owl.elev.angle_best = None


# def do_SET0(server, arg, owl):
#     SET0(owl)

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


# def do_get(server, arg, owl):
#     val, s = arg2val(arg)
#     #print(val, s)
#     if val is not None:
#         if arg.find("input_a=") > 0:
#             if val == '':
#                 val = 0
#             owl.input_azim = val
#             if arg.find("&max=") > 0:
#                 if val <= owl.azim.mover.angle_max_limit:
#                     if val > owl.azim.min_search:
#                         owl.azim.max_search = val
#                         save_config_search(owl)
#             elif arg.find("&min=") > 0:
#                 if val >= owl.azim.mover.angle_min_limit:
#                     if val < owl.azim.max_search:
#                         owl.azim.min_search = val
#                         save_config_search(owl)
#             else:
#                 owl.azim.angle_target = val
#                 if owl.rotor.timer is None:
#                     owl.azim.mover.go()
#         elif arg.find("input_e=") > 0:
#             if val == '':
#                 val = 0
#             owl.input_elev = val
#             if arg.find("&max=") > 0:
#                 if val <= owl.elev.mover.angle_max_limit:
#                     if val > owl.elev.min_search:
#                         owl.elev.max_search = val
#                         save_config_search(owl)
#             elif arg.find("&min=") > 0:
#                 if val >= owl.elev.mover.angle_min_limit:
#                     if val < owl.elev.max_search:
#                         owl.elev.min_search = val
#                         save_config_search(owl)
#             else:
#                 owl.elev.angle_target = val
#                 if owl.rotor.timer is None:
#                     owl.elev.mover.go()
#     owl.auto_start = False
# 
# 
# def do_get_config(server, arg, owl):
#     if USE_ROUTEROS_API:
#         val, s = arg2val(arg)
#         if val is not None:
#             if arg.find("ROUTEROS_IP=") >= 0:
#                 if val.count('.') == 3:
#                     if owl.ROUTEROS_IP != val:
#                         owl.ROUTEROS_IP = val
#             elif arg.find("ROUTEROS_USER=") >= 0:
#                 if owl.ROUTEROS_USER != val:
#                     owl.ROUTEROS_USER = val
#             elif arg.find("PASSWORD=") >= 0:
#                 if owl.ROUTEROS_PASSWORD != s:
#                     owl.ROUTEROS_PASSWORD = s
#             elif arg.find("RADIO_NAME=") >= 0:
#                 owl.RADIO_NAME = val
#                 if owl.ros_api:
#                     owl.ros_api.radio_name = b"=radio-name=" + owl.RADIO_NAME
#             owl.deinit_ros_api()
#             owl.init_ros_api(owl.ROUTEROS_USER, owl.ROUTEROS_PASSWORD, owl.ROUTEROS_IP)
# #             owl.deinit_ros_api2()
# #             owl.init_ros_api2(owl.ROUTEROS_USER, owl.ROUTEROS_PASSWORD, owl.ROUTEROS_IP)
# 
# 
# def do_get_config_WiFi(server, arg, owl):
#     val, s = arg2val(arg)
#     #print('val, arg', val, arg)
#     if val is not None:
#         if arg.find("SSID=") >= 0:
#             #if val in WiFi.ssid_list:
#             WiFi.SSID = val
#         elif arg.find("PASSWORD=") >= 0:
#             WiFi.PASSWORD = val
#         elif arg.find("OWL_IP=") >= 0:
#             val = val.lower()
#             if val.count('.') == 3 or val == 'dhcp':
#                 WiFi.OWL_IP = val
#                 if val.count('.') == 3:
#                     WiFi.OWL_GATEWAY = val[:val.rfind('.')] + '.1'
#                     WiFi.OWL_DNS = WiFi.OWL_GATEWAY
#         elif arg.find("OWL_SUBNET=") >= 0:
#             if val.count('.') == 3:
#                 WiFi.OWL_SUBNET = val
#         elif arg.find("OWL_GATEWAY=") >= 0:
#             if val.count('.') == 3:
#                 WiFi.OWL_GATEWAY = val
#                 if val.count('.') == 3:
#                     WiFi.OWL_DNS = WiFi.OWL_GATEWAY
#         elif arg.find("OWL_DNS=") >= 0:
#             if val.count('.') == 3:
#                 WiFi.OWL_DNS = val
#         else:
#             raise OwlError
# 
# 
# def do_get_config_speed(server, arg, owl):
#     val, s = arg2val(arg)
#     if val is not None:
#         if arg.find("azim_angle_accel_decel=") > 0:
#             owl.azim.mover.accel.angle_accel_decel = val
#         elif arg.find("azim_rpm_low=") > 0:
#             owl.azim.mover.rpm_low = val
#         elif arg.find("azim_rpm_high=") > 0:
#             owl.azim.mover.rpm_high = val
# 
#         elif arg.find("elev_angle_accel_decel=") > 0:
#             owl.elev.mover.accel.angle_accel_decel = val
#         elif arg.find("elev_rpm_low=") > 0:
#             owl.elev.mover.rpm_low = val
#         elif arg.find("elev_rpm_high=") > 0:
#             owl.elev.mover.rpm_high = val
# 
# 
# def do_get_debug(server, arg, owl):
#     s = get_arg(arg)
#     if arg.find("expression=") > 0:
#         owl.expression = s
# 
# 
# #--------------------------------------------------------
# def do_CW(server, arg, owl):
#     owl.azim.angle_target = round(owl.azim.angle_target + 1, 1)
#     if owl.rotor.timer is None:
#         owl.azim.mover.go()
#     owl.auto_start = False
# 
# 
# def do_CCW(server, arg, owl):
#     owl.azim.angle_target = round(owl.azim.angle_target - 1, 1)
#     if owl.rotor.timer is None:
#         owl.azim.mover.go()
#     owl.auto_start = False
# 
# 
# def do_UP(server, arg, owl):
#     owl.elev.angle_target = round(owl.elev.angle_target + 1, 1)
#     if owl.rotor.timer is None:
#         owl.elev.mover.go()
#     owl.auto_start = False
# 
# 
# def do_DOWN(server, arg, owl):
#     owl.elev.angle_target = round(owl.elev.angle_target - 1, 1)
#     if owl.rotor.timer is None:
#         owl.elev.mover.go()
#     owl.auto_start = False


def park(owl):
    print("Park")
    try:
        import config_parking
        print(config_parking.AZIM_PARKING_POSITION, config_parking.ELEV_PARKING_POSITION)
        if config_parking.AZIM_PARKING_POSITION is not None:
            owl.azim.angle_target = config_parking.AZIM_PARKING_POSITION
        if config_parking.ELEV_PARKING_POSITION is not None:
            owl.elev.angle_target = config_parking.ELEV_PARKING_POSITION
    except (ImportError, AttributeError) as e:
        print("ImportError: import config_parking:", e)
        owl.azim.angle_target = 0
        owl.elev.angle_target = 0
    owl.mode = owl.MD_MANUAL
