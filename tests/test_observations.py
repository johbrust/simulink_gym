from simulink_gym import SimulinkEnv, Observation, Observations
import numpy as np
import pytest

obs_1 = Observation(
    name="test_obs_1",
    low=0.0,
    high=1.0,
    parameter="test_parameter_1",
    value_setter=SimulinkEnv.set_workspace_variable,
    initial_value=0.5,
)

obs_2 = Observation(
    name="test_obs_2",
    low=-1.0,
    high=0.0,
    parameter="test_parameter_2",
    value_setter=SimulinkEnv.set_block_parameter,
    initial_value=-0.5,
)

observations = Observations([obs_1, obs_2])


def test_observations_get_item():
    obs = observations[0]
    assert obs.name == "test_obs_1"


def test_observations_iter():
    assert hasattr(observations, "__iter__")

    obs_names = []
    for obs in observations:
        obs_names.append(obs.name)
    assert obs_names == ["test_obs_1", "test_obs_2"]


def test_observations_len():
    assert len(observations) == 2


def test_observations_resample_all_initial_values():
    old_state = observations.initial_state
    observations.resample_all_initial_values()
    new_state = observations.initial_state
    assert any(old_state != new_state)


def test_observations_initial_state():
    set_values = np.array([0.77, -0.77], dtype=np.float32)
    observations.initial_state = set_values
    assert all(observations.initial_state == set_values)


def test_observations_initial_state_shape():
    set_values = np.array([[0.5], [-0.5]], dtype=np.float32)
    with pytest.raises(ValueError, match=r"Shape of values (.*) not equal to"):
        observations.initial_state = set_values


def test_observations_initial_state_range():
    set_values = np.array([0.5, 0.5], dtype=np.float32)
    with pytest.raises(ValueError, match=r".* not inside space limits .*"):
        observations.initial_state = set_values


def test_observation_reset_initial_state():
    # TODO: Only possible with running MATLAB session
    pass
