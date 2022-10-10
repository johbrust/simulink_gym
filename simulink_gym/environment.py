import os
import matlab.engine
import gym
import gym.spaces as spaces
from simulink_gym import logger, SIMULINK_BLOCK_LIB_PATH
import threading
import struct
import numpy as np
from typing import Optional, List, Union, Tuple
from pathlib import Path
from .utils import CommSocket, Observation, Observations, ParamBlock


class SimulinkEnv(gym.Env):

    _observations: Observations

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
                raise ValueError('Could not find model under {}'.format(self.model_path))
        self.model_dir = self.model_path.parent
        self.env_name = self.model_path.stem
        self.simulation_time = 0
        self.state = None
        self.terminated = True
        self.truncated = True
        self._simulation_alive = False
        self.model_debug = model_debug
        self.workspace_variables: List[Tuple] = []
        self.model_parameters: List[Tuple] = []

        # Create TCP/IP sockets and threads:
        self.recv_socket = CommSocket(recv_port)
        self.recv_socket_thread = threading.Thread()
        self.send_socket = CommSocket(send_port)
        self.send_socket_thread = threading.Thread()

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
                    logger.info('Creating simulation input object for model {}.slx'.format(self.env_name))
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

    def reset(self, seed: Optional[int] = None):
        super().reset(seed=seed)

        if self._simulation_alive:
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
                                                      args=(self.sim_input,), daemon=True)
            logger.debug('Starting simulation thread')
            self.simulation_thread.start()
            logger.debug('Simulation thread started')
            self._simulation_alive = True

        # Wait for connection to be established:
        logger.debug('Waiting for connection')
        self.send_socket_thread.join()
        self.recv_socket_thread.join()
        logger.debug('Connection established')

        # Reset truncated and terminated flags:
        self.truncated = False
        self.terminated = False

        return self.state

    def sim_step(self, action):
        if self._simulation_alive:
            # Execute action:
            self.send_data(np.array(action, ndmin=1))
            # Receive data:
            recv_data = self.recv_socket.receive()
            # When the simulation is truncated an empty message is sent:
            if not recv_data:
                self.truncated = True
                self.terminated = True
                self._simulation_alive = False
                logger.debug("Episode done.")
            else:
                self.state = np.array(recv_data[0:-1])
                self.simulation_time = recv_data[-1]  # simulation timestamp is last entry
                logger.debug(f'Simulation state: {self.state} ({self.simulation_time} s)')
        else:
            logger.info("No simulation running currently. No stepping possible.")

        return self.state, self.simulation_time, self.truncated, self.terminated

    def send_data(self, set_values: np.ndarray, stop=False):
        if set_values.shape == self.action_space.shape:
            set_values = set_values.flatten()
            byte_order_str = '<d' + 'd'*set_values.size
            msg = struct.pack(byte_order_str, int(stop), *set_values)
            logger.debug('Sending {}'.format(set_values))
            self.send_socket.send_msg(msg)
        elif not self._simulation_alive:
            logger.info("No simulation running currently. No data can be sent.")
        else:
            raise Exception(f"Wrong shape of data. The shape is {set_values.shape}, but should be {self.action_space.shape}.")

    @property
    def observations(self) -> Observations:
        return self._observations

    @observations.setter
    def observations(self, obs: List[Observation]):
        self._observations = Observations(obs)
        obs_dict = {observation.name: observation.space for observation in self._observations}
        self.observation_space = spaces.Dict(obs_dict)

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

    def set_block_parameter(self, block: ParamBlock):
        """Set parameter values of Simulink blocks.
        
        See: https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setblockparameter.html
        """
        if not self.model_debug:
            logger.debug(f'Setting parameter {block.parameter} of block {block.path} to value {block.value}')
            self.sim_input = self.matlab_engine.setBlockParameter(self.sim_input, block.path, block.parameter,
                                                                  str(block.value))

    def set_model_parameter(self, param: str, value: Union[int, float]):
        """Set Simulink model parameters.
        
        See: https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setmodelparameter.html
        """
        if not self.model_debug:
            logger.debug('Setting model parameter {} to value {:.3g}'.format(param, value))
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
                if not self.model_debug:  #TBD: Setting the initial values automatically if in model debug mode is not yet supported.
                    self.set_block_parameter(obs.param_block)
        except AttributeError:
            raise AttributeError('Environment observations not defined')

        return self.observations.initial_state

    def _send_stop_signal(self):
        set_values = np.zeros(self.action_space.shape)
        self.send_data(set_values, stop=True)
        self._simulation_alive = False

    def stop_simulation(self):
        if self._simulation_alive:
            self._send_stop_signal()
            # Receive data:
            _ = self.recv_socket.receive()
        if not self.model_debug and self.simulation_thread.is_alive():
            self.simulation_thread.join()

        self.truncated = True
        self._simulation_alive = False

    def open_sockets(self):
        logger.debug('Opening sockets')
        if self.recv_socket_thread.is_alive():
            logger.debug('recv_socket_thread already running')
        else:
            if self.recv_socket.is_connected():
                logger.debug('recv_socket still connected, closing socket')
                self.recv_socket.close()
            logger.debug('Creating and starting recv_socket thread')
            self.recv_socket_thread = threading.Thread(name='recv_socket.connect()', target=self.recv_socket.connect,
                                                       daemon=True)
            self.recv_socket_thread.start()

        if self.send_socket_thread.is_alive():
            logger.debug('send_socket_thread already running')
        else:
            if self.send_socket.is_connected():
                logger.debug('send_socket still connected, closing socket')
                self.send_socket.close()
            logger.debug('Creating and starting send_socket thread')
            self.send_socket_thread = threading.Thread(name='send_socket.connect()', target=self.send_socket.connect,
                                                       daemon=True)
            self.send_socket_thread.start()

    def close_sockets(self):
        logger.debug('Closing sockets')
        if self.recv_socket_thread.is_alive():
            self.recv_socket_thread.join()
        self.recv_socket.close()
        if self.send_socket_thread.is_alive():
            self.send_socket_thread.join()
        self.send_socket.close()

    def close(self):
        self.stop_simulation()
        logger.debug('Closing environment')
        # Close sockets:
        self.close_sockets()
        logger.debug('Environment closed')
