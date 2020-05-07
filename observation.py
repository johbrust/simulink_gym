import numpy as np
np.set_printoptions(linewidth=100, precision=3)


class Observation:

    def __init__(self, name, lower_sat=-np.inf, upper_sat=np.inf,
                 current_value=np.nan, previous_value=np.nan, normalize=False):
        self.name = name
        if lower_sat >= upper_sat:
            raise ValueError('Lower saturation value must be less than upper saturation value.')
        self.upper_saturation = upper_sat
        self.lower_saturation = lower_sat
        self.__current_value = current_value
        self.__previous_value = previous_value
        if self.lower_saturation > -np.inf and self.upper_saturation < np.inf and normalize:
            self.normalized = True
        else:
            self.normalized = False
        self.__previous_normalized_value, self.__current_normalized_value = self.normalize_values()

    def update_value(self, new_value):
        self.__previous_value = self.__current_value
        # Limit value:
        if new_value >= self.upper_saturation:
            self.__current_value = self.upper_saturation
        elif new_value <= self.lower_saturation:
            self.__current_value = self.lower_saturation
        else:
            self.__current_value = new_value
        # Calculate normalized values:
        self.__previous_normalized_value, self.__current_normalized_value = self.normalize_values()

    def normalize_values(self):
        if self.normalized:
            previous_normalized_value = (self.__previous_value - self.lower_saturation) / \
                                        (self.upper_saturation - self.lower_saturation)
            current_normalized_value = (self.__current_value - self.lower_saturation) / \
                                       (self.upper_saturation - self.lower_saturation)
            return previous_normalized_value, current_normalized_value
        else:
            return np.nan, np.nan

    def is_saturated(self):
        if self.__current_value >= self.upper_saturation:
            return True, 1
        elif self.__current_value <= self.lower_saturation:
            return True, -1
        else:
            return False, 0

    def was_saturated(self):
        if self.__previous_value >= self.upper_saturation:
            return True, 1
        elif self.__previous_value <= self.lower_saturation:
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

    def current_value(self):
        if self.normalized:
            return self.__current_normalized_value
        else:
            return self.__current_value

    def previous_value(self):
        if self.normalized:
            return self.__previous_normalized_value
        else:
            return self.__previous_value


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
        return np.array([[self.observations[i].current_value() for i in range(len(self.observations))]])

    def get_prev_obs_nparray(self):
        return np.array([[self.observations[i].previous_value() for i in range(len(self.observations))]])
