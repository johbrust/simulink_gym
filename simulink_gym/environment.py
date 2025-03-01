"""Simulink model environment wrapper implementing the Gym interface."""

import os
import threading
from pathlib import Path
from typing import Any, Union

import gymnasium as gym
import matlab.engine
import numpy as np

from . import SIMULINK_BLOCK_LIB_PATH, logger
from .observations import Observations
from .utils import CommSocket


class SimulinkEnv(gym.Env):
    """Wrapper class for using Simulink models through the Gym interface."""

    # Observations to be defined in child class:
    _observations: Observations

    def __init__(
        self,
        model_path: str,
        send_port: int = 42313,
        recv_port: int = 42312,
        model_debug: bool = False,
    ):
        """
        Simulink environment base class implementing the Gym interface.

        Args:
            model_path: path to the model file
            send_port: TCP/IP port for sending, default 42313
            recv_port: TCP/IP port for receiving, default 42312
            model_debug: flag for debugging simulink model files (.slx), default: False

        Raises:
            ValueError: if the model file does not exist
            RuntimeError: if the Matlab engine cannot be started
        """       
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            # Try as relative path:
            self.model_path = Path(os.path.abspath(model_path))
            if not self.model_path.exists():
                raise ValueError(f"Could not find model under {self.model_path}")
        self.model_dir = self.model_path.parent
        self.env_name = self.model_path.stem
        self.simulation_time = 0
        self.state = None
        self.model_debug = model_debug

        # Already prepared replacement for the done flag for Gym/Gymnasium>=0.26.0:
        self.terminated = True
        self.truncated = True

        # Create TCP/IP sockets for communication between model and Python wrapper:
        self.recv_socket = CommSocket(recv_port, "recv_socket")
        self.send_socket = CommSocket(send_port, "send_socket")

        if not self.model_debug:
            # Setup simulation thread and Matlab engine if not in debug mode:
            self.simulation_thread = threading.Thread()
            # Setup Matlab engine:
            logger.info("Starting Matlab engine")
            matlab_started = False
            start_trials = 0
            # Try to start Matlab engine:
            while not matlab_started and start_trials < 3:
                try:
                    self.matlab_engine = matlab.engine.start_matlab()
                except matlab.engine.RejectedExecutionError:
                    start_trials += 1
                    logger.error("Unable to start Matlab engine. Retrying...")
                else:
                    matlab_started = True
                    logger.info("Adding components to Matlab path")
                    self.matlab_path = self.matlab_engine.addpath(
                        str(SIMULINK_BLOCK_LIB_PATH)
                    )
                    self.matlab_path = self.matlab_engine.addpath(
                        str(self.model_dir.absolute())
                    )
                    # Create simulation as SimulationInput object:
                    logger.info(
                        f"Creating simulation input object for model "
                        f"{self.env_name}.slx"
                    )
                    self.sim_input = self.matlab_engine.Simulink.SimulationInput(
                        self.env_name
                    )
            if not matlab_started and start_trials >= 3:
                raise RuntimeError("Unable to start Matlab engine.")
        else:
            # Variables not needed in debug mode:
            self.simulation_thread = None
            self.matlab_engine = None
            self.matlab_path = None
            self.sim_input = None

    def __del__(self):
        """Deletion of environment needs to also quit the Matlab engine."""
        self.close()
        # Close matlab engine:
        if self.matlab_engine:
            self.matlab_engine.quit()

    @property
    def observations(self):
        """
        Getter method for observations.

        Returns: Observations object defining the observations
        """
        return self._observations

    @observations.setter
    def observations(self, observations: Observations):
        """
        Setter method for observations.

        Also sets the necessary observation space.

        Args:
            observations: Observations object defining the observations
        """
        self._observations = observations
        self.observation_space = self._observations.space

    def _reset(self):
        """
        Method implementing the generic reset behavior.

        This method stops a running simulation, closes and reopens the communication
        sockets and restarts the simulation.
        """
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.stop_simulation()

        self.close_sockets()
        self.open_sockets()

        self.state = self.set_initial_values()

        if not self.model_debug:
            # Create and start simulation thread:
            self.simulation_thread = threading.Thread(
                name="sim thread", target=self.matlab_engine.sim, args=(self.sim_input,)
            )
            self.simulation_thread.start()

        # Wait for connection to be established:
        self.send_socket.wait_for_connection()
        self.recv_socket.wait_for_connection()

        # Reset truncated and terminated flags:
        self.truncated = False
        self.terminated = False

    def reset(
        self, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Method required by the Gym interface to be implemented by the child class.

        The child implementation is supposed to call _reset() and has to return
        the state and info dictionary.

        Args:
            seed: seed for random number generation, default None
            options: options for resetting the environment, default None

        Returns:
            state: initial state sampled randomly from the observation space
            info: dict of auxiliary information
        """
        raise NotImplementedError

    def sim_step(self, action) -> tuple[np.ndarray, float, bool, bool]:
        """
        Stepping method for the Simulink model.

        This method implements the stepping of the Simulink model which should be called
        by the child implementation of the step method.

        Parameters:
            action
                action to be executed at the beginning of next simulation step, needs to
                match the defined action space

        Returns:
            state: current state of the environment (according to the observation space)
            simulation_time: current simulation time in seconds
            truncated: indicator for truncation condition (ending despite not reaching a
                terminal state)
            terminated: indicator for reaching a terminal state
        """
        if self.model_debug or self.simulation_thread.is_alive():
            # Check validity of action:
            if not self.action_space.contains(action):
                raise ValueError(f"Action {action} not in action space.")
            # Execute action:
            self.send_data(np.array(action))
            # Receive data:
            recv_data = self.recv_socket.receive()
            # When the simulation is truncated an empty message is received:
            if not recv_data:
                self.truncated = True
            else:
                if len(recv_data) == (self.observation_space.shape[0] + 1):
                    # Extract simulation state from received data:
                    self.state = np.array(recv_data[0:-1], ndmin=1, dtype=np.float32)
                    # Simulation timestamp is the last entry:
                    self.simulation_time = recv_data[-1]
                else:
                    logger.error(
                        f"Length of data received from the Simulink model invalid! "
                        f"Actual length is {len(recv_data)}, "
                        f"but should be {self.observation_space.shape[0] + 1}\n"
                        "There is possibly a problem with the block execution order of "
                        "the model (check project's known issues for more information)."
                    )
                    self.truncated = True
        else:
            # If the simulation is not alive, stepping is not possible and the
            # simulation most likely was already truncated.
            logger.warn("No simulation running currently. No stepping possible.")
            self.truncated = True

        return self.state, self.simulation_time, self.truncated, self.terminated

    def step(
        self, action
    ) -> tuple[np.ndarray, Union[int, float], bool, bool, dict[str, Any]]:
        """
        Method required by the Gym interface to be implemented by the child class.

        The child method is supposed to call sim_step().

        Args:
            action: action to be executed at the beginning of next simulation step,
                needs to match the defined action space

        Returns:
            state: current state of the environment (according to the observation space)
            reward: numerical reward signal from the environment for reaching current
                state
            terminated: flag indicating termination of the episode
            truncated: flag indicating truncation of the episode
            info:  dict of auxiliary information, e.g. simulation time
        """
        raise NotImplementedError

    def send_data(self, set_values: np.ndarray, stop: bool = False):
        """
        Method for sending the data to the Simulink model.

        Parameters
            set_values: numpy array containing the data, according to action space
            stop: flag for stopping the simulation, default: False
        """
        # Check validity of set_values and for running simulation:
        if set_values.shape == self.action_space.shape:
            if self.model_debug or self.simulation_thread.is_alive():
                self.send_socket.send_data(set_values, stop)
            else:
                logger.info("No simulation running currently. No data can be sent.")
        else:
            raise Exception(
                f"Wrong shape of data. The shape is {set_values.shape}, "
                f"but should be {self.action_space.shape}."
            )

    def set_workspace_variable(self, var: str, value: Union[int, float]):
        """
        Set variable in model workspace.

        Variables in the model workspace take precedence over variables in other
        workspaces. If blocks use variables from the workspace, their value can be set
        by using this function.

        See:
        https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setvariable.html

        Use this functionality sparsely as it can consume a lot of memory if
        executed often!

        Parameters:
            var: variable name
            value: value of the workspace variable
        """
        # Functionality only available if not in debug mode:
        if not self.model_debug:
            self.sim_input = self.matlab_engine.setVariable(
                self.sim_input, var, float(value), "Workspace", self.env_name
            )

    def set_block_parameter(self, path: str, value: Union[int, float]):
        """
        Set parameter values of Simulink blocks.

        See:
        https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setblockparameter.html

        Use this functionality sparsely as it can consume a lot of memory if
        executed often!

        Parameters:
            path: path of the block parameter
            value: value of the workspace variable
        """
        # Functionality only available if not in debug mode:
        if not self.model_debug:
            block_path = str(Path(path).parent)
            param = str(Path(path).stem)
            value = str(value)
            self.sim_input = self.matlab_engine.setBlockParameter(
                self.sim_input, block_path, param, value
            )

    def set_model_parameter(self, param: str, value: Union[int, float]):
        """
        Set Simulink model parameters.

        See:
        https://www.mathworks.com/help/simulink/slref/simulink.simulationinput.setmodelparameter.html

        Use this functionality sparsely as it can consume a lot of memory if
        executed often!

        Parameters:
            param: parameter name
            value: value of the model parameter
        """
        # Functionality only available if not in debug mode:
        if not self.model_debug:
            self.sim_input = self.matlab_engine.setModelParameter(
                self.sim_input, param, str(value)
            )

    def set_initial_values(self):
        """
        Set the initial values of the state/observations.

        Used for resetting the environment.

        Returns:
            initial state according to observation space
        """
        try:
            # Functionality only available if not in debug mode:
            if not self.model_debug:
                self.observations.reset_values()
        except AttributeError:
            raise AttributeError("Environment observations not defined")

        return self.observations.initial_state

    def _send_stop_signal(self):
        """Method for sending the stop signal to the simulation."""
        set_values = np.zeros(self.action_space.shape)
        self.send_data(set_values, stop=True)

    def stop_simulation(self):
        """Method for stopping the simulation."""
        if self.model_debug or self.simulation_thread.is_alive():
            try:
                self._send_stop_signal()
            except Exception:
                # Connection already lost
                logger.info(
                    "Stop signal could not be sent, connection probably already dead"
                )
            else:
                # Clear receive data queue:
                _ = self.recv_socket.receive()
            finally:
                if not self.model_debug:
                    self.simulation_thread.join()

        self.truncated = True

    def open_sockets(self):
        """Method for opening the sockets for communication with the simulation."""
        self.recv_socket.open_socket()
        self.send_socket.open_socket()

    def close_sockets(self):
        """Method for closing the sockets for communication with the simulation."""
        self.recv_socket.close()
        self.send_socket.close()

    def close(self):
        """Method for closing/shutting down the simulation."""
        self.stop_simulation()
        # Close sockets:
        self.close_sockets()

    def render(self):
        """
        Render method recommended by the Gym interface.

        Since Simulink models don't share a common representation suitable for rendering
        such a method is not possible to implement.
        """
        logger.info("Rendering not supported for Simulink models.")
