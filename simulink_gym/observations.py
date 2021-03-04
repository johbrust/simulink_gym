import numpy as np  # TODO: define dependencies


class Observation:

    def __init__(self, name, lower_sat=-np.inf, upper_sat=np.inf,
                 current_value=np.nan, previous_value=np.nan, normalize=False):
        self._name = name
        if lower_sat >= upper_sat:
            raise ValueError('Lower saturation value must be less than upper saturation value.')
        self.upper_saturation = upper_sat
        self.lower_saturation = lower_sat
        self._current_value = current_value
        self._previous_value = previous_value
        if self.lower_saturation > -np.inf and self.upper_saturation < np.inf and normalize:
            self.normalized = True
        else:
            self.normalized = False
        self._previous_normalized_value, self._current_normalized_value = self.normalize_values()

    def update_value(self, new_value):
        self._previous_value = self._current_value
        # Limit value:
        if new_value >= self.upper_saturation:
            self._current_value = self.upper_saturation
        elif new_value <= self.lower_saturation:
            self._current_value = self.lower_saturation
        else:
            self._current_value = new_value
        # Calculate normalized values:
        self._previous_normalized_value, self._current_normalized_value = self.normalize_values()

    def normalize_values(self):
        if self.normalized:
            previous_normalized_value = (self._previous_value - self.lower_saturation) / \
                                        (self.upper_saturation - self.lower_saturation)
            current_normalized_value = (self._current_value - self.lower_saturation) / \
                                       (self.upper_saturation - self.lower_saturation)
            return previous_normalized_value, current_normalized_value
        else:
            return np.nan, np.nan

    def is_saturated(self):
        if self._current_value >= self.upper_saturation:
            return True, 1
        elif self._current_value <= self.lower_saturation:
            return True, -1
        else:
            return False, 0

    def was_saturated(self):
        if self._previous_value >= self.upper_saturation:
            return True, 1
        elif self._previous_value <= self.lower_saturation:
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

    @property
    def current_value(self):
        if self.normalized:
            return self._current_normalized_value
        else:
            return self._current_value

    @property
    def previous_value(self):
        if self.normalized:
            return self._previous_normalized_value
        else:
            return self._previous_value

    def __str__(self):
        return self._name


class Observations:

    def __init__(self, *args: Observation):
        self._observations = list()
        for obs in args:
            self._observations.append(obs)

    def update_observations(self, new_values):
        for i in range(len(self._observations)):
            if new_values is not None:
                self._observations[i].update_value(new_values[i])
            else:
                self._observations[i].update_value(np.nan)

    def get_current_obs(self):
        return np.array([[self._observations[i].current_value for i in range(len(self._observations))]])

    @property
    def observation_names(self):
        return [str(obs) for obs in self._observations]

    def observation(self, observation: str):
        try:
            obs_index = self.observation_names.index(observation)
        except ValueError as e:
            raise e
        else:
            return self._observations[obs_index]

    def __dict__(self):
        return {str(self._observations[i]): self._observations[i].current_value
                for i in range(len(self._observations))}

    def get_prev_obs(self):
        return np.array([[self._observations[i].previous_value() for i in range(len(self._observations))]])

    def __len__(self):
        return len(self._observations)

    def __str__(self):
        return ', '.join('{}: {:.3g}'.format(str(obs), obs.current_value) for obs in self._observations)
