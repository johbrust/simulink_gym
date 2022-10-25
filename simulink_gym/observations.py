from gym.spaces import Box
from typing import Union, List
from .utils import BlockParam
import numpy as np


class Observation:
    def __init__(
        self,
        name: str,
        low: float,
        high: float,
        initial_value_path: str,
        initial_value: Union[int, float] = None,
        reinitialize = False
    ):
        self.name = name
        self.space = Box(low=np.array([low], dtype=np.float32), high=np.array([high], dtype=np.float32))

        if initial_value is None:
            initial_value = self.space.sample()
        else:
            initial_value = np.array([initial_value], dtype=np.float32)

        if not self.space.contains(initial_value):
            raise ValueError(
                f"Observation {self.name}: Initial value {initial_value} not inside space limits"
            )

        self.reinitialize = reinitialize
        self.block_param = BlockParam(initial_value_path, initial_value)

    @property
    def initial_value(self):
        return self.block_param.value

    @initial_value.setter
    def initial_value(self, value):
        self.block_param.value = value

    def resample_initial_value(self):
        self.block_param.value = self.space.sample()


class Observations:
    def __init__(self, observations: List[Observation]):
        self._observations = observations
        lows = np.array([observation.space.low[0] for observation in self._observations], dtype=np.float32)
        highs = np.array([observation.space.high[0] for observation in self._observations], dtype=np.float32)
        self.space = Box(low=lows, high=highs)

    def __getitem__(self, index: int):
        return self._observations[index]

    def __iter__(self):
        return self._observations.__iter__()

    def __next__(self):
        return self._observations.__next__()

    def __len__(self):
        return len(self._observations)

    @property
    def initial_state(self):
        initial_state = [obs.initial_value[0] for obs in self._observations]
        return np.array(initial_state)
