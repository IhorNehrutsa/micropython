from steps_per_rev import StepsPerRev

class StepperLimit(StepsPerRev):
    def __init__(self, steps_per_rev = 1, steps_max_limit=None, steps_min_limit=None, angle_max_limit=None, angle_min_limit=None):
        super().__init__(steps_per_rev)

        self.steps_max_limit = steps_max_limit  # физические механические ограничения конструкции
        self.steps_min_limit = steps_min_limit

        self.angle_max_limit = angle_max_limit  # физические механические ограничения конструкции
        if angle_max_limit is not None:
            self.steps_max_limit = self.angle_to_steps(angle_max_limit)  # физические механические ограничения конструкции

        self.angle_min_limit = angle_min_limit
        if angle_min_limit is not None:
            self.steps_min_limit = self.angle_to_steps(angle_min_limit)

        self._steps_now = 0
        self._steps_target = 0

        self._direction = 0  # (-1, 0, 1) текущее направление вращения, устанавливается в dir()

    def __repr__(self):
        if angle_max_limit is not None and angle_min_limit is not None:
            return f"StepperLimit(steps_per_rev={self.steps_per_rev}, angle_max_limit={self.angle_max_limit}, angle_min_limit={self.angle_min_limit})"
        else:
            return f"StepperLimit(steps_per_rev={self.steps_per_rev}, steps_max_limit={self.steps_max_limit}, steps_min_limit={self.steps_min_limit})"

    # -----------------------------------------------------------------------
#     @property
#     def reverse_direction(self):
#         return self._reverse_direction
# 
#     #@micropython.native
#     @reverse_direction.setter
#     def reverse_direction(self, reverse_direction:int):
#         self._reverse_direction = 1 if bool(reverse_direction) else 0

    # -----------------------------------------------------------------------
    #@micropython.native
    @property
    def steps_now(self) -> int:
        return self._steps_now

    #@micropython.native
    @property
    def steps_target(self) -> int:
        return self._steps_target

    #@micropython.native
    @steps_target.setter
    def steps_target(self, steps_target):
        # Set the target position that will be executed in the main loop
        #print(f"Stepper():steps_target.setter({steps_target})")
        if self.steps_max_limit is not None:
            if steps_target > self.steps_max_limit:
                steps_target = self.steps_max_limit
        if self.steps_min_limit is not None:
            if steps_target < self.steps_min_limit:
                steps_target = self.steps_min_limit
        self._steps_target = steps_target

    # -----------------------------------------------------------------------
    @property
    def direction(self) -> int:
        return self._direction

    #@micropython.native
    @direction.setter
    def direction(self, delta:int):
        if delta > 0:
            self._direction = 1
            self.pin_dir(1 ^ self._reverse_direction)
        elif delta < 0:
            self._direction = -1
            self.pin_dir(0 ^ self._reverse_direction)
        else:
            self._direction = 0
        #print(f'{self.name} Set direction:delta={delta} to self._direction={self._direction} with self._reverse_direction={self._reverse_direction} self.pin_dir()={self.pin_dir()}')

    #@micropython.native
    def is_ready(self) -> bool:
        return self._steps_target == self._steps_now
