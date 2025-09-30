from utime import time

import config
from Owl_API import *
from skt import close_socket


def handle_communication(owl):
    if owl.state == owl.CM_NO:
        #if owl.сounter == 0:
        if owl.mode == owl.MD_SECTOR_A:
            if owl.sector_time is not None:
                if time() - owl.sector_time > 30:
                    owl.sector_time = time()
                    owl.speed += owl.speed_dir
                    #owl.azim.mover.pid.output_limits = (owl.azim_output_limits[0] * owl.speed // 10, owl.azim_output_limits[1] * owl.speed // 10)
                    #print('owl.azim.mover.pid.output_limits', owl.azim.mover.pid.output_limits)
                    if (owl.speed <= 1) or (owl.speed >= 10):
                        owl.speed_dir = -owl.speed_dir

    elif owl.state in (owl.CM_SEE, owl.CM_READ):
        #owl.corr.execute()
        pass
    elif owl.state == owl.CM_READ:
        pass
    elif owl.state == owl.CM_DETECT:
        pass
    elif owl.state == owl.CM_SECTOR:
        pass
    elif owl.state == owl.CM_STAY:
        pass
    elif owl.state == owl.CM_ESCORT:
        pass
    else:
        raise ValueError('owl.state={}'.format(owl.state))
