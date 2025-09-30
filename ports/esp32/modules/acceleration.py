
class Trapezoidal:
    # yapf: disable
    def __init__(
        self,
        name='',
        startpoint=0,
        setpoint=0,
        angle_accel_decel=5,
        min_output = 0,
        max_output = 10_000
    ):
    # yapf: enable
        self.name=name
        self.startpoint = startpoint
        self.setpoint = setpoint

        self.angle_accel_decel = angle_accel_decel
        self.min_output = min_output
        self.max_output = max_output

        self._last_output = None
        self._last_input = None
        self._last_error = None

    #@micropython.native
    def __call__(self, input_):

        # compute error terms
        error = min(abs(self.startpoint - input_), abs(self.setpoint - input_))
        output = self.max_output
        if error < self.angle_accel_decel:
            output = self.min_output + (self.max_output  - self.min_output) * error / self.angle_accel_decel

        if output < self.min_output:
            output = self.min_output
        if output < 100:
            output = 100
        
        # keep track of state
        self._last_input = input_
        self._last_error = error
        self._last_output = output

        return output

    def info(self):
        return 'startpoint={} setpoint={} last_input={} last_error={} last_output={}'.format(self.startpoint, self.setpoint, self._last_input, self._last_error, self._last_output)

    def __repr__(self):
        # yapf: disable
        return (
            '{}('
            'startpoint={}, '
            'setpoint={}, '
            'angle_accel_decel={}, '
            'min_output={}, '
            'max_output={}'
            ')'
        ).format(self.__class__.__name__,
            self.startpoint,
            self.setpoint,
            self.angle_accel_decel,
            self.min_output,
            self.max_output
        )
        # yapf: enable

#     def write(self):
#         f = open("config_speed.py", "x")
#         f.write("\n{}_accel_{}_angle_accel_decel = {}".format(
#             self.name.replace(' ', ''),
#             self.__class__.__name__,
#             self.angle_accel_decel
#             ))
#         f.write("\n{}_accel_{}_min_output = {}".format(
#             self.name.replace(' ', ''),
#             self.__class__.__name__,
#             self.min_output
#             ))
#         f.write("\n{}_accel_{}_max_output = {}".format(
#             self.name.replace(' ', ''),
#             self.__class__.__name__,
#             self.max_output
#             ))
#         f.close()
# 
#     def read(self):
#         try:
#             import config_speed
#             print(dir(config_speed))
#             print(config_speed.Elev_Trapezoidal_angle_accel_decel)
#             s = 'config_speed.'+self.name.replace(' ', '')+'_'+self.__class__.__name__+'_angle_accel_decel'
#             #s = 'a=config_speed.'+self.name.replace(' ', '_')+'_'+self.__class__.__name__+'_angle_accel_decel'
#             # s = self.name.replace(' ', '_')+'_'+self.__class__.__name__+'_angle_accel_decel'
#             print('s=', s)
#             self.angle_accel_decel = eval(s)
#             exec(s)
#             print('self.angle_accel_decel=', self.angle_accel_decel)
#             self.angle_accel_decel = eval('config_speed.'+self.name.replace(' ', '_')+'_'+self.__class__.__name__+'_angle_accel_decel')
#             print('self.angle_accel_decel=', self.angle_accel_decel)
# #             self.min_output =
# #             self.max_output =
# #
#             del (config_speed)
#         except ImportError as e:
#             print("ImportError: import config_speed: ", e)

# t = Trapezoidal(name="Elev  ")
# t.write()
# t = Trapezoidal(name="Azim  ")
# t.write()
# print(t)
# print(t.info())
#
# print('READ')
# t.read()
