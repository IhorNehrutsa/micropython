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
        for j in range(self.length):
            self.values[j] = 0
        self.sum = 0
        self.i = 0
        self.is_full = False

    def update(self, value):
        self.sum -= self.values[self.i]
        self.values[self.i] = value
        self.i += 1
        if self.i >= self.length:
            self.i = 0
            self.is_full = True
        self.sum += value

    def average(self):
        if self.is_full:
            return self.sum / self.length
        elif self.i > 0:
            return self.sum / self.i
        else:
            return 0
