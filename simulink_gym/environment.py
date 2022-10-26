import os
import matlab.engine
import gym
from simulink_gym import logger, SIMULINK_BLOCK_LIB_PATH
import threading
import numpy as np
from typing import List, Union, Tuple
from pathlib import Path
from .observations import Observations
from .utils import CommSocket, BlockParam


class SimulinkEnv(gym.Env):

    observations: Observations

    def __init__(self,
                 model_path: str,
                 send_port=42313,
                 recv_port=42312,
                 model_debug=False):
        """Define an environment.

        Parameters:
            model_path : str
                path to the model file
            send_port : int, default 42313
                TCP/IP port for sending
            recv_port : int, default 42312
                TCP/IP port for receiving
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            # Try as relative path:
            self.model_path = Path(os.path.abspath(model_path))
            if not self.model_path.exists():
                raise ValueError(f'Could not find model under {self.model_path}')
        self.model_dir = self.model_path.parent
        self.env_name = self.model_path.stem
        self.simulation_time = 0
        self.state = None
        self.terminated = True
        self.truncated = True
        self.model_debug = model_debug
        self.workspace_variables: List[Tuple] = []
        self.model_parameters: List[Tuple] = []

        # Create TCP/IP sockets:
        self.recv_socket = CommSocket(recv_port, 'recv_socket')
        self.send_socket = CommSocket(send_port, 'send_socket')

        if not self.model_debug:
            # Create simulation thread:
            self.simulation_thread = threading.Thread()

            # Setup Matlab engine:
            logger.info('Starting Matlab engine')
            matlab_started = False
            start_trials = 0
            while not matlab_started and start_trials < 3:
                try:
                    self.matlab_engine = matlab.engine.start_matlab()
                except matlab.engine.RejectedExecutionError:
                    start_trials += 1
                    logger.error('Unable to start Matlab engine. Retrying...')
                else:
                    matlab_started = True
                    logger.info(f'Adding components to Matlab path')
                    self.matlab_path = self.matlab_engine.addpath(str(SIMULINK_BLOCK_LIB_PATH))
                    self.matlab_path = self.matlab_engine.addpath(str(self.model_dir.absolute()))
                    # Create simulation input object:
                    logger.info(f'Creating simulation input object for model {self.env_name}.slx')
                    self.sim_input = self.matlab_engine.Simulink.SimulationInput(self.env_name)
            if not matlab_started and start_trials >= 3:
                raise RuntimeError('Unable to start Matlab engine.')
        else:
            self.simulation_thread = None
            self.matlab_engine = None
            self.matlab_path = None
            self.sim_input = None

    def __del__(self):
        self.close()
        # Close matlab engine:
        if self.matlab_engine is not None:
            self.matlab_engine.quit()

    def _reset(self):  #, seed: Optional[int] = None):
        # super().reset(seed=seed)

        if self.simulation_thread.is_alive():
            self.stop_simulation()

        self.close_sockets()
        self.open_sockets()

        # Set initial values:
        self.state = self.set_initial_values()

        if not self.model_debug:
            # Set model parameters and workspace variables:
            self._set_model_parameters()
            self._set_workspace_variables()
            # Create and start simulation thread:
            logger.debug('Creating simulation thread')
            self.simulation_thread = threading.Thread(name='sim thread', target=self.matlab_engine.sim,
                                                      args=(self.sim_input,))
            logger.debug('Starting simulation thread')
            self.simulation_thread.start()
            logger.debug('Simulation thread started')

        # Wait for connection to be established:
        self.send_socket.wait_for_connection()
        self.recv_socket.wait_for_connection()

        # Reset truncated and terminated flags:
        self.truncated = False
        self.terminated = False

    def reset(self):
        raise NotImplementedError

    def sim_step(self, action):
        if self.simulation_thread.is_alive():
            # Check validity of action:
            if not self.action_space.contains(action):
                raise ValueError(f"Action {action} not in action space.")
            # Execute action:
            self.send_data(np.array(action))
            # Receive data:
            recv_data = self.recv_socket.receive()
            # When the simulation is truncated an empty message is sent:
            if not recv_data:
                self.truncated = True
                self.terminated = True
                logger.debug("Episode done.")
            else:
                self.state = np.array(recv_data[0:-1], dtype=np.float32)
                self.simulation_time = recv_data[-1]  # simulation timestamp is last entry
                logger.debug(f'Simulation state: {self.state} ({self.simulation_time} s)')
        else:
            logger.info("No simulation running currently. No stepping possible.")

        return self.state, self.simulation_time, self.truncated, self.terminated

    def step(self, action):
        raise NotImplementedError

    def send_data(self, set_values: np.ndarray, stop=False):
        if set_values.shape == self.action_space.shape and self.simulation_thread.is_alive():
            self.send_socket.send_data(set_values)
        elif not self.simulation_thread.is_alive():
            logger.debug("No simulation running currently. No data can be sent.")
        else:
            raise Exception(f"Wrong shape of data. The shape is {set_values.shape}, but should be {self.action_space.shape}.")

    def set_workspace_variable(self, var, value):
        """Set variable in model workspace.

        Variables in the model workspace take precedence over variables in other workspaces. If blocks use
        variables from the workspace, their value can be set by using this function.
        
        See: https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setvariable.html
        """
        if not self.model_debug:
            logger.debug(f'Setting variable {var} to {value} in model workspace')
            self.sim_input = self.matlab_engine.setVariable(self.sim_input, var, value, 'Workspace', self.env_name)

    def _set_workspace_variables(self):
        """Set all workspace variables."""
        for var, value in self.workspace_variables:
            self.set_workspace_variable(var, value)

    def set_block_parameter(self, parameter: BlockParam):
        """Set parameter values of Simulink blocks.
        
        See: https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setblockparameter.html
        """
        if not self.model_debug:
            block_path = str(Path(parameter.parameter_path).parent)
            param = str(Path(parameter.parameter_path).stem)
            value = str(parameter.value)
            logger.debug(f'Setting parameter {param} of block {block_path} to value {value}')
            self.sim_input = self.matlab_engine.setBlockParameter(self.sim_input, block_path, param,
                                                                  value)

    def set_model_parameter(self, param: str, value: Union[int, float]):
        """Set Simulink model parameters.
        
        See: https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setmodelparameter.html
        """
        if not self.model_debug:
            logger.debug(f'Setting model parameter {param} to value {value:.3g}')
            self.sim_input = self.matlab_engine.setModelParameter(self.sim_input, param, str(value))

    def _set_model_parameters(self):
        """Set all model parameters."""
        for parameter, value in self.model_parameters:
            self.set_model_parameter(parameter, value)

    def set_initial_values(self):
        """Set the initial values of the state/observations.        
        """
        try:
            for obs in self.observations:
                if not self.model_debug and obs.reinitialize:  #TBD: Setting the initial values automatically if in model debug mode is not yet supported.
                    self.set_block_parameter(obs.block_param)
        except AttributeError:
            raise AttributeError('Environment observations not defined')

        return self.observations.initial_state

    def _send_stop_signal(self):
        set_values = np.zeros(self.action_space.shape)
        self.send_data(set_values, stop=True)

    def stop_simulation(self):
        if self.simulation_thread.is_alive():
            self._send_stop_signal()
            # Clear receive data queue:
            _ = self.recv_socket.receive()
            if not self.model_debug:
                self.simulation_thread.join()

        self.truncated = True

    def open_sockets(self):
        logger.debug('Opening sockets')
        self.recv_socket.open_socket()
        self.send_socket.open_socket()

    def close_sockets(self):
        logger.debug('Closing sockets')
        self.recv_socket.close()
        self.send_socket.close()

    def close(self):
        self.stop_simulation()
        logger.debug('Closing environment')
        # Close sockets:
        self.close_sockets()
        logger.debug('Environment closed')

    def render(self):
        pass
