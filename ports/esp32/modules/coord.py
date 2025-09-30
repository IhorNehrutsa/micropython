class Coordinate():
    def __init__(self, mover, max_search=180, min_search=-180):
        self.mover = mover
        # self.circle_diagram = [0 for i in range(360)]
        self.circle_diagram = 0  # {ros_param: [0 for i in range(int(360/angle_resolution))] for ros_param in ros_params}
        self.t = 0

        self.search_dir = 1  # исходное направление поиска положительное (вправо или вверх)
        self.search_dir_next = self.search_dir

        self.state = -1
        self.state_prev = -1

        self._angle_start = None  # стартовая позиция
        self.angle_start_plus = None
        self.angle_start_minus = None
        self.value_start = {}  # исходное значение в начале поиска
        self.avg_start = {}  # среднее значение в начале поиска

        self.angle_plus = None
        self.value_plus = {}  # значение в конце поиска в "положительном" направлении

        self.angle_minus = None
        self.value_minus = {}  # значение в конце поиска в "отрицательном" направлении

        self.angle_best = None
        self.avg_best = {}  # среднее значение в лучшей позиции

        self.angle_bisector_diff = None  #  угол посередине участка плато
        self.avg_bisector_diff = {}

        self.angle_bisector_max = None  # угол посередине участка из максимальных значений
        self.avg_bisector_max = {}

        self.on_correct(self.correct_handler)

        self.max_search = max_search  # сектор поиска заданный оператором должен быть уже, чем физические механические ограничения конструкции
        self.min_search = min_search

    def __repr__(self):
        return f"Coordinate({super().__repr__()}, max_search={self.max_search}, min_search={self.min_search})"

    def correct_handler(self, delta_angle):
        def to180(a):
            return a

        #print("1 correct_handler", self.angle_start, self.angle_minus, self.angle_plus, delta_angle)
        if self.angle_start is not None:
            self.angle_start = to180(self.angle_start + delta_angle)
        if self.angle_minus is not None:
            self.angle_minus = to180(self.angle_minus + delta_angle)
        if self.angle_plus is not None:
            self.angle_plus = to180(self.angle_plus + delta_angle)
        if self.angle_best is not None:
            self.angle_best = to180(self.angle_best + delta_angle)
        if self.angle_bisector_max is not None:
            self.angle_bisector_max = to180(self.angle_bisector_max + delta_angle)
        if self.angle_bisector_diff is not None:
            self.angle_bisector_diff = to180(self.angle_bisector_diff + delta_angle)
        if self.angle_start_plus is not None:
            self.angle_start_plus = to180(self.angle_start_plus + delta_angle)
        if self.angle_start_minus is not None:
            self.angle_start_minus = to180(self.angle_start_minus + delta_angle)
        #print("2 correct_handler", self.angle_start, self.angle_minus, self.angle_plus, delta_angle)

    # -----------------------------------------------------------------------
    def on_correct(self, handler):
        # Set correction handler
        self._on_correct_handler = handler

    def correct_angles(self, delta_angle):
        if self._on_correct_handler:
            self._on_correct_handler(delta_angle)

    @property
    def angle_start(self):
        return self._angle_start

    @angle_start.setter
    def angle_start(self, angle):
        self.set_angle_start(angle)

    def set_angle_start(self, angle):
        self._angle_start = max(min(angle, self.max_search), self.min_search)


class CoordinateShow(Coordinate):
    def __init__(self, mover, max_search=180, min_search=-180):
        super().__init__(mover, max_search, min_search)

    @property
    def angle_target(self):
        #print(f'{self.mover.name} CoordinateShow():angle_target.property')
        return self.mover.angle_target

    @angle_target.setter
    def angle_target(self, angle_target):
        #print(f'{self.mover.name} CoordinateShow():angle_target.setter')
        #print(f'{self.mover.name} CoordinateShow():angle_target.setter self.mover.angle_target={self.mover.angle_target} self.max_search={self.max_search}')
        if self.mover.angle_target != angle_target:
            self.mover.angle_target = max(min(angle_target, self.max_search), self.min_search)
#             if self.mover.angle_now < self.mover.angle_target:
#                 print('+++', self.mover.name, self.mover.angle_target)
#             else:
#                 print('---', self.mover.name, self.mover.angle_target)
            #print(f'self.mover={self.mover}')
            #print(f'{self.mover.name} CoordinateShow():angle_target.setter self.mover.angle_target={self.mover.angle_target} self.max_search={self.max_search}')
