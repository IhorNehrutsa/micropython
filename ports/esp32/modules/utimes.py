#import sys
from utime import ticks_us , ticks_diff

is_micropython = True
'''
Resolution of timer is 2^30 microseconds
2^30 = 1 073 741 824 microseconds
2^30/1000000 = 1073.74 seconds
2^30/1000000/60 = 17.89 minuts
The timer overloads every 17.89 minutes !!!
'''
#mask = sys.maxsize >> 1
#mask = 0x3fffFFF

#times_us = lambda: ticks_us() # lambda is slower then @micropython.native


#@micropython.native
@micropython.viper
def times_us() -> object:
    return ticks_us()


#@micropython.native
@micropython.viper
def times_ms() -> int:
    return int(ticks_us()) // 1000


#@micropython.native
@micropython.viper
def times_s() -> int:
    return int(ticks_us()) // 1000000


@micropython.native
#@micropython.viper
def timed_function(f, *args, **kwargs):
    try:
        myname = str(f).split(' ')[1]
    except IndexError as e:
        print("IndexError :", e)
        print("Hint: @micropython.viper or @micropython.native functions do not have name")
        return

    def new_func(*args, **kwargs):
        t = ticks_us()
        result = f(*args, **kwargs)
        delta = ticks_diff(ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta / 1000))
        return result

    return new_func
