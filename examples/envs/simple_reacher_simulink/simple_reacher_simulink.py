from simulink_gym import SimulinkEnv, Observation, Observations
from gym.spaces import Box
from pathlib import Path
import numpy as np
import math


class SimpleReacherSimulink(SimulinkEnv):
    def __init__(self, length_1=1.0, length_2=0.5):
        super().__init__(
            model_path=Path(__file__)
            .parent.absolute()
            .joinpath("simple_reacher_simulink.slx"),
        )

        self.set_block_parameter(f"{self.env_name}/length_1/Value", length_1)
        self.set_block_parameter(f"{self.env_name}/length_2/Value", length_2)

        # Define action space:
        self.action_space = Box(low=0.0, high=math.pi, shape=(2,), dtype=np.float32)

        # Define observation space:
        self.observations = Observations(
            [
                Observation(
                    "x",
                    -np.inf,
                    np.inf,
                    f"{self.env_name}/IC_1/Value",
                    self.set_block_parameter,
                ),
                Observation(
                    "y",
                    -np.inf,
                    np.inf,
                    f"{self.env_name}/IC_2/Value",
                    self.set_block_parameter,
                ),
            ]
        )

        # Get initial state from defined observations:
        self.state = self.observations.initial_state

    def reset(self):
        # Call common reset:
        super()._reset()

        # Return reshaped state. Needed for use as tf.model input:
        return self.state

    def step(self, action):
        state, simulation_time, terminated, truncated = self.sim_step(action)

        # Check all termination conditions:
        done = bool(terminated or truncated)

        # Receive reward for every step inside state and time limits:
        reward = 0

        info = {"simulation time [s]": simulation_time}

        return state, reward, done, info
