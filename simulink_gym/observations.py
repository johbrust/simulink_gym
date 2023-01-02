from gym.spaces import Box
from typing import Any, Callable, Union, List
import numpy as np
from . import logger


class Observation:
    """Class for representation of environment observations."""

    def __init__(
        self,
        name: str,
        low: float,
        high: float,
        parameter: str,
        value_setter: Callable[[str, Union[int, float]], Any],
        initial_value: Union[int, float] = None,
    ):
        """Class representing environment observations.

        Block parameter values can be either defined directly in the block, if the value
        path is available programmatically (check MATLAB/Simulink documentation for that
        matter), or indirectly by using a workspace variable. For this, define a
        variable in the model workspace and set the block parameter value to this
        variable. The value can then be set programmatically by setting the workspace
        variable. Depending on this, set the value_setter method accordingly.

        Parameters:
            name: string
                name of the observation
            low: float
                lower boundary of the observation value, can also be -numpy.inf, used to
                define the observation space
            high: float
                higher boundary of the observation value, can also be numpy.inf, used to
                define the observation space
            parameter: string
                path of the block parameter for setting the initial value (if setting
                the block value directly) or name of the workspace variable used for the
                block parameter
            value_setter: Callable
                method for setting the initial value, either
                SimulinkEnv.set_block_parameter or SimulinkEnv.set_workspace_variable
            initial_value: int or float, default: None
                initial value of the observation (see BlockParam.value), the value
                will be sampled from the observation space if None
        """
        self.name = name
        self.space = Box(low=low, high=high, shape=(1,), dtype=np.float32)

        self.initial_value = initial_value if initial_value else self.space.sample()[0]
        self.parameter = parameter
        self._value_setter = value_setter

    def _check_initial_value(self, value):
        value = np.array(value, ndmin=1, dtype=np.float32)
        if not self.space.contains(value):
            raise ValueError(
                f"Observation {self.name}: "
                f"Initial value {value} not inside space limits "
                f"([{self.space.low}, {self.space.high}]). "
                f"{self.space.shape}, {value.shape}"
            )

    @property
    def initial_value(self):
        """Initial value of the observation."""
        return self._initial_value

    @initial_value.setter
    def initial_value(self, value):
        """Set method for the initial value"""
        logger.debug(f"Setting {self.name} to {value}")
        self._check_initial_value(value)
        self._initial_value = value

    def resample_initial_value(self):
        """Resample the initial value according to observation space."""
        self._initial_value = self.space.sample()[0]

    def reset_value(self):
        """Set the initial value in the simulation object."""
        self._value_setter(self.parameter, self.initial_value)


class Observations:
    """Class representing multiple environment observations as a list."""

    def __init__(self, observations: List[Observation]):
        """Class representing multiple environment observations as a list.

        Parameters:
            observations: list of observations
        """
        self._observations = observations
        # Create combined observation space from single observations:
        lows = np.array(
            [observation.space.low[0] for observation in self._observations],
            dtype=np.float32,
        )
        highs = np.array(
            [observation.space.high[0] for observation in self._observations],
            dtype=np.float32,
        )
        self.space = Box(low=lows, high=highs)

    def __getitem__(self, index: int):
        """Method for indexing of observations list."""
        return self._observations[index]

    def __iter__(self):
        """Method for iterating over observations list."""
        return self._observations.__iter__()

    def __next__(self):
        """Method for getting next observation in list."""
        return self._observations.__next__()

    def __len__(self):
        """Method for determining number of observations."""
        return len(self._observations)

    def resample_all_initial_values(self):
        """Resampling all observations."""
        self.initial_state = self.space.sample()

    @property
    def initial_state(self):
        """Combined initial state of all observations as numpy array."""
        initial_state = [obs.initial_value for obs in self._observations]
        return np.array(initial_state, ndmin=1, dtype=np.float32)

    @initial_state.setter
    def initial_state(self, values: np.ndarray):
        """Set method for the initial state"""
        if values.shape == self.space.shape:
            for index, observation in enumerate(self._observations):
                observation.initial_value = values[index]
        else:
            raise ValueError(
                f"Shape of values ({values.shape}) not equal to "
                f"shape of observations ({self.space.shape})"
            )

    def reset_values(self):
        """Reset all observation values to their initial values."""
        for obs in self._observations:
            obs.reset_value()
