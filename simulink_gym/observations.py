from gym.spaces import Box
from typing import Union, List
from .utils import BlockParam
import numpy as np
from simulink_gym import logger


class Observation:
    """Class for representation of environment observations."""

    def __init__(
        self,
        name: str,
        low: float,
        high: float,
        initial_value_path: str,
        initial_value: Union[int, float] = None
    ):
        """Class representing environment observations.
        
        Parameters:
            name: string
                name of the observation
            low: float
                lower boundary of the observation value, can also be -numpy.inf, used to
                define the observation space
            high: float
                higher boundary of the observation value, can also be numpy.inf, used to
                define the observation space
            initial_value_path: string
                path of the block parameter for setting the initial value (see BlockParam.parameter_path)
            initial_value: int or float, default: None
                initial value of the observation (see BlockParam.value), the value will be sampled
                from the observation space if None
        """
        self.name = name
        self.space = Box(low=low, high=high, shape=(1,), dtype=np.float32)

        # Sample initial value if not defined:
        if initial_value is None:
            initial_value = self.space.sample()[0]
        else:
            initial_value = initial_value

        self._check_initial_value(initial_value)

        self.block_param = BlockParam(initial_value_path, initial_value)

    def _check_initial_value(self, value):
        value = np.array(value, ndmin=1, dtype=np.float32)
        if not self.space.contains(value):
            raise ValueError(
                f"Observation {self.name}: Initial value {value} not inside space limits ([{self.space.low}, {self.space.high}]). {self.space.shape}, {value.shape}"
            )

    @property
    def initial_value(self):
        """Initial value of the observation."""
        return self.block_param.value

    @initial_value.setter
    def initial_value(self, value):
        """Set method for the initial value"""
        logger.debug(f'Setting {self.name} to {value}')
        self._check_initial_value(np.array(value, ndmin=1, dtype=np.float32))
        self.block_param.value = value

    def resample_initial_value(self):
        """Resample the initial value according to observation space."""
        self.block_param.value = self.space.sample()[0]


class Observations:
    """Class representing multiple environment observations as a list."""
    
    def __init__(self, observations: List[Observation]):
        """Class representing multiple environment observations as a list.
        
        Parameters:
            observations: list of observations
        """
        self._observations = observations
        # Create combined observation space from single observations:
        lows = np.array([observation.space.low[0] for observation in self._observations], dtype=np.float32)
        highs = np.array([observation.space.high[0] for observation in self._observations], dtype=np.float32)
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
        return np.array(initial_state)

    @initial_state.setter
    def initial_state(self, values: np.ndarray):
        """Set method for the initial state"""
        if values.shape == self.space.shape:
            for index, observation in enumerate(self._observations):
                observation.initial_value = values[index]
        else:
            raise ValueError(f"Shape of values ({values.shape}) not equal to shape of observations ({self.space.shape})")
