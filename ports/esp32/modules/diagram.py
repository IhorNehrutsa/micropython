'''
diff = value[i+1] - value[i]
                            motor.bisector_diff_angle
                            |   motor.bisector_max_angle
                            |   |
                            |   v
                            v  ___max value                            _
                 _____________/   \_______                           _/ \_ 
                /             ^   ^       \max diff                _/     \_
    ___________/              |   |        \______________       _/         \_
___/           ^              |   |        ^              \_____/             \____
               |              |   |        |
indexes:max_ diff             |   |        min_diff
                       left_max   right_max

'''


def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0


class Diagram():
    def __init__(self):
        self.NoData()

    def NoData(self):
        self.value = []  # значения параметра "ros_param" "value"[i] соответствующее позиции "angle"[i]
        self.diff = []  # разность значений ("value"[i+1] - "value"[i])
        self.gradient = []  # напрвление изменения параметра "ros_param": 0, -1, +1

        self.index_max_diff = None  # индекс с наибольшим увеличением(ростом) значения параметра "ros_param" "value"
        self.index_min_diff = None  # индекс с наибольшим уменьшением(падением) значения параметра "ros_param" "value"

        self.index_left_max = None  # меньший(левый) индекс с наибольшим значением параметра "ros_param" "value"
        self.index_right_max = None  # больший(правый) индекс с наибольшим значением параметра "ros_param" "value"

        self.min_value = -999999
        self.max_value = +999999  # максимальное значение параметра "ros_param" вообще из всех

        self.count_max_value_peaks = 0  # количество пиков(горбов) на графике параметра "ros_param" "value"
        self.peak_index = []  # индексы пиков из максимальных значений параметра "ros_param" в виде кортежей (index_left_max, index_right_max)

        #self.avg_value = 0  # усредненное значения параметра "ros_param" в целевом направлении в диапазоне от index_max_diff до index_min_diff

    def len(self):
        return len(self.value)

    def calc_min_max_value(self):
        if self.len() > 0:
            self.min_value = min(self.value)
            self.max_value = max(self.value)
        else:
            self.min_value = -999999
            self.max_value = +999999

    def clear(self):
        self.value.clear()
        self.diff.clear()
        self.gradient.clear()

    def append(self, val):
        self.value.append(val)

    def pop(self, i):
        self.value.pop(i)
        self.diff.pop(i)
        self.gradient.pop(i)

    def is_same_gradient(self, i):
        if (self.gradient[i] == 0) \
        and (self.gradient[i+1] != 0) \
        and (self.gradient[i+1] == self.gradient[i+2]) \
        and (self.gradient[i+3] == 0):
            return True
        return False

    def count_same_value(self, i):
        count = 1
        val = self.value[i]
        i -= 1
        while i >= 0:
            if val == self.value[i]:
                count += 1
                i -= 1
            else:
                break
        return count

    def remove_same_value(self):
        i = self.len() - 1
        while i > 1:
            n = self.count_same_value(i)
            while n > 2:
                self.value.pop(i - 1)
                i -= 1
                n -= 1
            i -= 1

    def calc_diff_gradient(self):
        self.diff.clear()
        self.gradient.clear()
        for i in range(len(self.value) - 1):
            v1_v = self.value[i + 1] - self.value[i]
            self.diff.append(v1_v)
            self.gradient.append(sign(v1_v))

        self.diff.insert(0, +0.5)  # Для случая, если на графике идет только снижение сигнала (гладко понижающийся график),
        self.gradient.insert(0, 1)  # то увеличение задаем вручную в самом начале

        self.diff.append(-0.5)  # Для случая, если на графике идет только увеличение сигнала (гладко повышающийся график),
        self.gradient.append(-1)  # то уменьшение задаем вручную в самом конце

    def calc_indexes(self):
        if self.len() <= 0:
            self.NoData()
            return
        # ищем плато с наибольшим ростом сигнала
        # ищем индекс с последним наибольшим ростом сигнала
        max_diff = max(self.diff)
        count_max_diff = self.diff.count(max_diff)
        self.index_max_diff = 0
        start = 0
        for i in range(count_max_diff):
            self.index_max_diff = self.diff.index(max_diff, start)
            start = self.index_max_diff + 1

        # ищем индекс с первым наибольшим падением сигнала
        min_diff = min(self.diff)
        self.index_min_diff = self.diff.index(min_diff) - 1  # из-за добавки в начале

        # вычисляем среднее значение на плато
        #d = self.index_min_diff - self.index_max_diff + 1
        #self.avg_value = sum(self.value[self.index_max_diff:self.index_min_diff + 1]) / d

        # вычисляем "левый" и "правый" индексы максимального значения
        self.calc_min_max_value()
        # ищем все пики из максимальных значений
        self.peak_index = []
        i = 0
        while i < self.len():
            if self.value[i] == self.max_value:
                index_left_max = i
                index_right_max = i
                while (index_right_max < (len(self.value) - 1)) and (self.value[index_right_max + 1] == self.max_value):
                    index_right_max += 1
                    i += 1
                self.peak_index.append((index_left_max, index_right_max))
                i += 1
            else:
                i += 1
        self.count_max_value_peaks = len(self.peak_index)

        #print("diagram: max_value, index_max_diff, index_min_diff, count_max_diff", self.max_value, self.index_max_diff, self.index_min_diff, count_max_diff)
        ok = False
        if self.index_max_diff < self.index_min_diff:
            try:
                self.index_left_max = self.value.index(self.max_value, self.index_max_diff, self.index_min_diff)
                ok = True
            except ValueError:
                pass
        elif self.index_max_diff == self.index_min_diff:
            try:
                self.index_left_max = self.value.index(self.max_value, self.index_max_diff, self.index_min_diff + 1)
                ok = True
            except ValueError:
                pass
        if ok:
            print("Пик внутри плато - The peak inside the plateau")
            self.index_right_max = self.index_left_max
            while (self.index_right_max < len(self.value) - 1) and (self.value[self.index_right_max + 1] == self.max_value):
                self.index_right_max += 1
        else:
            self.index_max_diff = None
            self.index_min_diff = None
            print("Средний пик - Average peak")
            l = len(self.peak_index)
            i = l // 2 + l % 2 - 1
            self.index_left_max, self.index_right_max = self.peak_index[i]
