#from micropython import const
from math import sqrt, degrees, atan2


@micropython.native
def to360(degree):
    while degree >= 360:
        degree -= 360
    while degree < 0:
        degree += 360
    return degree


@micropython.native
def to180(degree):
    while degree >= 180:
        degree -= 360
    while degree < -180:
        degree += 360
    return degree


#  AN3461.pdf
#===============================================================================
#  GetAngle - Converts accleration data to pitch & roll & yaw
#===============================================================================
@micropython.native
def calc_yaw_pitch_roll(x, y, z):  # x, y, z - Accelerometer output
    try:
        yaw = atan2(sqrt(x * x + y * y), z)  # θ
    except ZeroDivisionError:
        yaw = 0

    try:
        pitch = atan2(x, sqrt(y * y + z * z))  # ρ
    except ZeroDivisionError:
        pitch = 0

    try:
        roll = atan2(y, sqrt(x * x + z * z))  # φ
    except ZeroDivisionError:
        roll = 0
    # convert radians into degrees
    return degrees(yaw), degrees(pitch), degrees(roll)


@micropython.native
def calc_pitch(x, y, z):  # x, y, z - Accelerometer output
    try:
        return degrees(atan2(x, sqrt(y * y + z * z)))  # ρ
    except ZeroDivisionError:
        return 0


@micropython.native
def calc_roll(x, y, z):  # x, y, z - Accelerometer output
    try:
        return degrees(atan2(y, sqrt(x * x + z * z)))  # φ
    except ZeroDivisionError:
        return 0
