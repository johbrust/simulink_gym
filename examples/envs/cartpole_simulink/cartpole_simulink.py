from simulink_gym import SimulinkEnv, Observation, Observations
from gym.spaces import Discrete
from pathlib import Path
import numpy as np
import math


# Define example environment:
class CartPoleSimulink(SimulinkEnv):
    """Classic Cart Pole Control Environment implemented in Matlab/Simulink.

    With Simulink solver settings matching the Gym implementation this environment
    produces identical trajectories (up to numerical accuracy).

    Observation:
        Type: Box(4)
        Num     Observation               Min                     Max
        0       Cart Position             -4.8                    4.8
        1       Cart Velocity             -Inf                    Inf
        2       Pole Angle                -0.418 rad (-24 deg)    0.418 rad (24 deg)
        3       Pole Angular Velocity     -Inf                    Inf

    Actions:
        Type: Discrete(2)
        Num   Action
        0     Push cart to the left
        1     Push cart to the right

        Note: The amount the velocity that is reduced or increased is not
        fixed; it depends on the angle the pole is pointing. This is because
        the center of gravity of the pole increases the amount of energy needed
        to move the cart underneath it

    Reward:
        Reward is 1 for every step taken, including the termination step
    """

    def __init__(
        self,
        stop_time: float = 10.0,
        step_size: float = 0.02,
        model_debug: bool = False,
    ):
        """Simulink implementation of the classic Cart Pole environment.

        Parameters:
            stop_time: float, default 10
                maximum simulation duration in seconds
            step_size: float, default 0.02
                size of simulation step in seconds
            model_debug: bool, default False
                Flag for setting up the model debug mode (see Readme.md for details)
        """
        super().__init__(
            model_path=Path(__file__)
            .parent.absolute()
            .joinpath("cartpole_simulink.slx"),
            model_debug=model_debug,
        )

        # Define action space:
        self.action_space = Discrete(2)

        # Define state and observations:
        self.max_cart_position = 2.4
        max_pole_angle_deg = 12
        self.max_pole_angle_rad = max_pole_angle_deg * math.pi / 180.0
        self.observations = Observations(
            [
                Observation(
                    "pos",
                    -self.max_cart_position * 2.0,
                    self.max_cart_position * 2.0,
                    f"{self.env_name}/Integrator_position/InitialCondition",
                    self.set_block_parameter,
                ),
                Observation(
                    "vel",
                    -np.inf,
                    np.inf,
                    f"{self.env_name}/Integrator_speed/InitialCondition",
                    self.set_block_parameter,
                ),
                Observation(
                    "theta",
                    -self.max_pole_angle_rad * 2.0,
                    self.max_pole_angle_rad * 2.0,
                    f"{self.env_name}/Integrator_theta/InitialCondition",
                    self.set_block_parameter,
                ),
                Observation(
                    "omega",
                    -np.inf,
                    np.inf,
                    f"{self.env_name}/Integrator_omega/InitialCondition",
                    self.set_block_parameter,
                ),
            ]
        )

        # Get initial state from defined observations:
        self.state = self.observations.initial_state

        # Set simulation parameters:
        self.set_model_parameter("StopTime", stop_time)
        self.set_workspace_variable("step_size", step_size)

    def reset(self):
        # Resample initial state:
        self.observations.initial_state = np.random.uniform(
            low=-0.05, high=0.05, size=(4,)
        )

        # Call common reset:
        super()._reset()

        # Return reshaped state. Needed for use as tf.model input:
        return self.state

    def step(self, action):
        """Method for stepping the simulation."""

        action = int(action)

        state, simulation_time, terminated, truncated = self.sim_step(action)

        # Check all termination conditions:
        current_pos = state[0]
        current_theta = state[2]
        done = bool(
            terminated
            or truncated
            or current_pos < -self.max_cart_position
            or current_pos > self.max_cart_position
            or current_theta < -self.max_pole_angle_rad
            or current_theta > self.max_pole_angle_rad
        )

        # Receive reward for every step inside state and time limits:
        reward = 1

        info = {"simulation time [s]": simulation_time}

        return state, reward, done, info
