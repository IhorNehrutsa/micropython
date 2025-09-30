# txt_srv.py

from json import dumps


def owl_id(server, owl):
    return dumps((owl.ID, owl.state, owl.сounter)) + '\n'


def owl_angle(server, owl):
    s = str(owl.mode) + '-' + str(owl.azim.state) + '-' + str(owl.elev.state) + '-' + str(owl.corr.state) + '-' + str(owl.state) + '-' + str(owl.сounter)
    return dumps((s, round(owl.azim.mover.angle_now, 1), round(owl.elev.mover.angle_now, 1), owl.ROUTEROS_IP, owl.RADIO_NAME, round(owl.azim.angle_target, 1), round(owl.elev.angle_target, 1), owl.value_now, owl.SSID)) + '\n'  #, owl.filter_avg()


def _owl_pid(mover, pid):
    return dumps((pid.setpoint, mover._last_time, pid._last_input, pid._last_output, pid._last_error, pid.tunings, pid.output_limits, pid.output_pads, pid.components)) + '\n'


def owl_azim_pid(server, owl):
    return _owl_pid(owl.azim.mover, owl.azim.mover.pid)


def owl_elev_pid(server, owl):
    return _owl_pid(owl.elev.mover, owl.elev.mover.pid)
