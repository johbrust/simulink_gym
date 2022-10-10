from gym import Space
from typing import Union, List
from pathlib import Path
from .param_block import ParamBlock
import numpy as np


class Observation:
    def __init__(
        self,
        name: str,
        space: Space,
        initial_value_path: str,
        initial_value: Union[int, float] = None,
    ):
        self.name = name
        self.space = space
        block_path = str(Path(initial_value_path).parent)
        parameter = str(Path(initial_value_path).stem)

        if initial_value is None:
            initial_value = self.space.sample()
        else:
            initial_value = np.array([initial_value], dtype=np.float32)

        if not self.space.contains(initial_value):
            raise ValueError(
                f"Observation {self.name}: Initial value {initial_value} not inside space limits"
            )

        self.param_block = ParamBlock(block_path, parameter, initial_value)

    @property
    def initial_value(self):
        return self.param_block.value

    @initial_value.setter
    def initial_value(self, value):
        self.param_block.value = value

    def resample_initial_value(self):
        self.param_block.value = self.space.sample()


class Observations:
    def __init__(
        self,
        observations: List[Observation]
    ):
        self._observations = observations

    @property
    def observations(self):
        return self._observations

    @observations.setter
    def observations(self, observations):
        self._observations = observations

    def __iter__(self):
        return self._observations.__iter__()

    def __next__(self):
        return self._observations.__next__()

    @property
    def initial_state(self):
        initial_state = [obs.initial_value for obs in self._observations]
        return np.array(initial_state)
