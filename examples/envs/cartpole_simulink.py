from simulink_gym import SimulinkEnv, Observation, BlockParam
from gym.spaces import Box, Discrete
from pathlib import Path
import numpy as np
import math


# Define example environment:
class CartPoleSimulink(SimulinkEnv):
    """Classic Cart Pole Control Environment implemented in Matlab/Simulink.
    
    #TBD: This implementation should correspond to the original Gym implementation.
    """

    def __init__(self, continuous_action=False, model_debug=False, stop_time=100):
        super().__init__(
            model_path=Path(__file__).parent.absolute().joinpath("cartpole_simulink.slx"),
            model_debug=model_debug,
        )

        # Define model parameters to set:
        self.model_parameters = [
            ('StopTime', stop_time)
        ]

        # Define workspace variables to set:
        self.workspace_variables = [
            ('g', 9.08665),
            ('length_pole', 0.5),
            ('mass_cart', 1.0),
            ('mass_pole', 0.1),
        ]

        # Define action space:
        self.continuous_action = continuous_action
        abs_max_force_N = 10.0
        self.set_block_parameter(BlockParam(f'{self.env_name}/ForceGain/Gain', abs_max_force_N))
        if self.continuous_action:
            self.action_space = Box(low=-1.0, high=1.0, shape=(1,))
        else:
            # self.action_space = Discrete(3, start=-1)
            self.action_space = Discrete(3)

        # Define state and observations:
        self.max_cart_position = 1.0
        max_pole_angle_deg = 8
        self.max_pole_angle_rad = max_pole_angle_deg*math.pi/180.0
        self.observations = [
            Observation("theta",
                        Box(low=-self.max_pole_angle_rad, high=self.max_pole_angle_rad, shape=(1,)),
                        f'{self.env_name}/Integrator_theta/InitialCondition'),
            Observation("omega",
                        Box(low=-np.inf, high=np.inf, shape=(1,)),
                        f'{self.env_name}/Integrator_omega/InitialCondition',
                        0.0),
            Observation("alpha",
                        Box(low=-np.inf, high=np.inf, shape=(1,)),
                        f'{self.env_name}/IC1/Value',
                        0.0),
            Observation("pos", 
                        Box(low=-self.max_cart_position, high=self.max_cart_position, shape=(1,)),
                        f'{self.env_name}/Integrator_position/InitialCondition',
                        0.0),
            Observation("vel",
                        Box(low=-np.inf, high=np.inf, shape=(1,)),
                        f'{self.env_name}/Integrator_speed/InitialCondition',
                        0.0),
            Observation("acc",
                        Box(low=-np.inf, high=np.inf, shape=(1,)),
                        f'{self.env_name}/IC/Value',
                        0.0)
        ]

        # Get initial state from defined observations:
        self.state = self.observations.initial_state

    def reset(self):
        # Resample initial state of theta:
        self.observations.observations[0].resample_initial_value()

        # Call common reset:
        state = super().reset()

        state = {"theta": state[0], "omega": state[1], "alpha": state[2], "pos": state[3], "vel": state[4], "acc": state[5]}

        # Return reshaped state. Needed for use as tf.model input:
        # return state.reshape((1, len(self.observations)))
        return state

    def step(self, action):
        """Method for stepping the simulation."""

        if self.continuous_action:
            action = np.array(action, ndmin=1, dtype=self.action_space.dtype)
        else:
            action = int(action)
        
        state, simulation_time, terminated, truncated = self.sim_step(action)

        # Check all termination conditions:
        current_theta = state[0]
        current_pos = state[3]
        terminated = bool(
            terminated or
            current_pos < -self.max_cart_position
            or current_pos > self.max_cart_position
            or current_theta < -2.0*self.max_pole_angle_rad
            or current_theta > 2.0*self.max_pole_angle_rad
        )

        # Receive reward for every step inside state limits:
        reward = 1

        info = {"simulation time [s]": simulation_time}
        
        # Reshape state needed for use as tf.model input:
        state = np.array(state, dtype=np.float32)
        state = {"theta": np.array([state[0]], dtype=np.float32),
                 "omega": np.array([state[1]], dtype=np.float32),
                 "alpha": np.array([state[2]], dtype=np.float32),
                 "pos": np.array([state[3]], dtype=np.float32),
                 "vel": np.array([state[4]], dtype=np.float32),
                 "acc": np.array([state[5]], dtype=np.float32)}
        return state, reward, (terminated or truncated), info
