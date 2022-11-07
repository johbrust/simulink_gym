from simulink_gym import SimulinkEnv, Observation, Observations
from gym.spaces import Discrete
from pathlib import Path
import numpy as np
import math


# Define example environment:
class CartPoleSimulink(SimulinkEnv):
    """Classic Cart Pole Control Environment implemented in Matlab/Simulink.
    
    #TBD: This implementation should correspond to the original Gym implementation.
    """

    def __init__(self, model_debug=False, stop_time=100):
        super().__init__(
            model_path=Path(__file__).parent.absolute().joinpath("cartpole_simulink.slx"),
            model_debug=model_debug,
        )

        # TBD: Currently disabled functionality causing memory issues:
        # Define model parameters to set:
        # self.model_parameters = [
        #     ('StopTime', stop_time)
        # ]

        # TBD: Currently disabled functionality causing memory issues:
        # Define workspace variables to set:
        # self.workspace_variables = [
        #     ('g', 9.08665),
        #     ('length_pole', 0.5),
        #     ('mass_cart', 1.0),
        #     ('mass_pole', 0.1),
        # ]

        # Define action space:
        self.action_space = Discrete(2)

        # Define state and observations:
        self.max_cart_position = 2.4
        max_pole_angle_deg = 12
        self.max_pole_angle_rad = max_pole_angle_deg*math.pi/180.0
        self.observations = Observations([
            Observation("pos", 
                        -self.max_cart_position * 2.0,
                        self.max_cart_position * 2.0,
                        f'{self.env_name}/Integrator_position/InitialCondition'),
            Observation("vel",
                        -np.inf,
                        np.inf,
                        f'{self.env_name}/Integrator_speed/InitialCondition'),
            Observation("theta",
                        -self.max_pole_angle_rad * 2.0,
                        self.max_pole_angle_rad * 2.0,
                        f'{self.env_name}/Integrator_theta/InitialCondition'),
            Observation("omega",
                        -np.inf,
                        np.inf,
                        f'{self.env_name}/Integrator_omega/InitialCondition'),
        ])
        self.observation_space = self.observations.space

        # Get initial state from defined observations:
        self.state = self.observations.initial_state

    def reset(self):
        # Resample initial state of theta:
        for observation in self.observations:
            observation.resample_initial_value()

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
        terminated = bool(
            terminated or
            current_pos < -self.max_cart_position
            or current_pos > self.max_cart_position
            or current_theta < -2.0*self.max_pole_angle_rad
            or current_theta > 2.0*self.max_pole_angle_rad
        )

        # Receive reward for every step inside state and time limits:
        reward = 1

        info = {"simulation time [s]": simulation_time}
        
        return state, reward, (terminated or truncated), info
