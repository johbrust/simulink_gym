import numpy as np
np.set_printoptions(linewidth=100)


class Observation:

    def __init__(self, name, lower_saturation=-np.inf, upper_saturation=np.inf,
                 current_value=np.nan, previous_value=np.nan):
        self.name = name
        # TODO: Is upper_saturation > lower_saturation?
        self.upper_saturation = upper_saturation
        self.lower_saturation = lower_saturation
        self.current_value = current_value
        self.previous_value = previous_value

    def update_value(self, new_value):
        self.previous_value = self.current_value
        # Limit value:
        if new_value >= self.upper_saturation:
            self.current_value = self.upper_saturation
        elif new_value <= self.lower_saturation:
            self.current_value = self.lower_saturation
        else:
            self.current_value = new_value

    def is_saturated(self):
        if self.current_value >= self.upper_saturation:
            return True, 1
        elif self.current_value <= self.lower_saturation:
            return True, -1
        else:
            return False, 0

    def was_saturated(self):
        if self.previous_value >= self.upper_saturation:
            return True, 1
        elif self.previous_value <= self.lower_saturation:
            return True, -1
        else:
            return False, 0

    def will_saturate_further(self, new_direction):
        is_already_saturated, direction = self.is_saturated()
        if is_already_saturated:
            return direction == new_direction
        else:
            return False

    def did_saturate_further(self, new_direction):
        was_already_saturated, direction = self.was_saturated()
        if was_already_saturated:
            return direction == new_direction
        else:
            return False


class Observations:

    def __init__(self, *args: Observation):
        self.observations = list()
        for obs in args:
            self.observations.append(obs)

    def update_observations(self, new_values):
        for i in range(len(self.observations)):
            if new_values is not None:
                self.observations[i].update_value(new_values[i])
            else:
                self.observations[i].update_value(np.nan)

    def get_current_obs_nparray(self):
        return np.array([[self.observations[i].current_value for i in range(len(self.observations))]])

    def get_prev_obs_nparray(self):
        return np.array([[self.observations[i].previous_value for i in range(len(self.observations))]])
