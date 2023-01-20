from simulink_gym import SimulinkEnv, Observation
from gym.spaces import Box
import numpy as np
import pytest

obs = Observation(
    name="test_obs",
    low=0.0,
    high=1.0,
    parameter="test_parameter",
    value_setter=SimulinkEnv.set_workspace_variable,
    initial_value=0.5,
)


def test_observation_name():
    assert obs.name == "test_obs"


def test_observation_space():
    space = Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
    assert obs.space == space


def test_observation_parameter():
    assert obs.parameter == "test_parameter"


def test_observation_value_setter():
    assert obs._value_setter == SimulinkEnv.set_workspace_variable


def test_observation_initial_value():
    assert obs.initial_value == 0.5


def test_observation_initial_value_above_range():
    with pytest.raises(ValueError, match=r".* not inside space limits .*"):
        obs.initial_value = 1.5


def test_observation_initial_value_below_range():
    with pytest.raises(ValueError, match=r".* not inside space limits .*"):
        obs.initial_value = -0.5


def test_observation_resample_initial_value():
    old_value = obs.initial_value
    obs.resample_initial_value()
    assert not (old_value == obs.initial_value)


def test_observation_reset_initial_value():
    # TODO: Only possible with running MATLAB session
    pass
