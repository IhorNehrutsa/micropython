'''
Фильтр скользящего среднего 
Moving average filter 
http://www.autex.spb.su/download/dsp/dsp_guide/ch15en-ru.pdf
'''


class MovingAverageFilter():
    def __init__(self, length=20):
        self.length = length
        self.values = [0] * length  # 1
        self.clear()  # 2

    def clear(self):
        for i in range(self.length):
            self.values[i] = 0
        self.sum = 0
        self._i = 0
        self.is_full = False

    def update(self, value):
        self.sum -= self.values[self._i]
        self.values[self._i] = value
        self._i += 1
        if self._i >= self.length:
            self._i = 0
            self.is_full = True
        self.sum += value

    def average(self):
        if self.is_full:
            return self.sum / self.length
        elif self._i > 0:
            return self.sum / self._i
        else:
            return 0

    def __repr__(self):
        # yapf: disable
        return (
            '{}('
            'length={}, sum={}, average={}'
            ')'
        ).format(self.__class__.__name__,
            self.length,self.sum, self.average(),
        )
        # yapf: enable
