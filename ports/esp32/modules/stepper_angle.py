from stepper import Stepper
from steps_per_rev import StepsPerRev

class StepperAngle(Stepper, StepsPerRev):
    def __init__(self, name, pin_step, pin_dir, freq=5_000, reverse_direction=0, max_limit=180, min_limit=-180, steps_per_rev=1):
        super().__init__(name, pin_step, pin_dir, freq, reverse_direction)

        self.steps_per_rev = steps_per_rev  # перезапись для StepsPerRev

        self.angle_max_limit = max_limit  # физические механические ограничения конструкции
        if max_limit is not None:
            self.steps_max_limit = self.angle_to_steps(max_limit)  # физические механические ограничения конструкции

        self.angle_min_limit = min_limit
        if min_limit is not None:
            self.steps_min_limit = self.angle_to_steps(min_limit)

    def __repr__(self):
        return f"StepperAngle(max_limit={self.angle_max_limit}, min_limit={self.angle_min_limit}, steps_per_rev={self.steps_per_rev}):" + super().__repr__()

    #@micropython.native
    @property
    def angle_now(self):
        return self.steps_to_angle(self.steps_now)

    #@micropython.native
    @property
    def angle_target(self):
        # print(f'{self.name} StepperAngle():angle_target.property')
        return self.steps_to_angle(self._steps_target)

    @angle_target.setter
    def angle_target(self, angle_target):
        # Set the target position that will be executed in the main loop
        # print(f'{self.name} StepperAngle():angle_target.setter angle_target={angle_target}')
        self.steps_target = self.angle_to_steps(angle_target)
