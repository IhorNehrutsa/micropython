
PI2 = 3.14159265358979 * 2


class StepsPerRev():
    def __init__(self, steps_per_rev=1):
        self.steps_per_rev = steps_per_rev

    def __repr__(self):
        return f"StepsPerRev(steps_per_rev={self.steps_per_rev})"

    @micropython.native
    def angle_to_steps(self, angle) -> int:
        return round(self.steps_per_rev * angle / 360)

    @micropython.native
    def steps_to_angle(self, steps) -> float:
        return steps * 360 / self.steps_per_rev

    @micropython.native
    def radian_to_steps(self, angle) -> int:
        return round(self.steps_per_rev * angle / PI2)

    @micropython.native
    def steps_to_radian(self, steps) -> float:
        return steps * PI2 / self.steps_per_rev

    @micropython.native
    def f_to_rps(self, f) -> float:  # rotates per second  # об/с
        return f / self.steps_per_rev

    @micropython.native
    def f_to_rpm(self, f) -> float:  # rotates per minute  # об/мин
        return f * 60 / self.steps_per_rev

    @micropython.native
    def rps_to_f(self, rps) -> float:
        return rps * self.steps_per_rev

    @micropython.native
    def rpm_to_f(self, rpm) -> float:
        return rpm * self.steps_per_rev / 60

    @micropython.native
    def f_to_rpm_(self, f, steps_per_rev) -> float:  # rotates per minute  # об/мин
        return f * 60 / steps_per_rev

    @micropython.native
    def f_to_rps_(self, f, steps_per_rev) -> float:  # rotates per second  # об/с
        return f / steps_per_rev

