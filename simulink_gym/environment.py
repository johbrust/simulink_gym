import socket
import os
import matlab.engine  # TODO: define dependencies
import gym  # TODO: define dependencies
from gym import logger  # TODO: define dependencies
import threading
import struct
import array
from pathlib import Path
from collections import namedtuple
from .observations import Observations
from .actions import Actions

logger.set_level(logger.DEBUG)


param_block = namedtuple('block', ['path', 'param', 'value'])


class Environment(gym.Env):
    def __init__(self, model_path: str, send_port=42313, recv_port=42312, model_debug=False):
        """Define an environment.

        Parameters:
            model_path : str
                path to the model file
            send_port : int, default 42313
                TCP/IP port for sending
            recv_port : int, default 42312
                TCP/IP port for receiving
        """
        # TODO: check input value validity
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            # Try as relative path:
            self.model_path = Path(os.path.abspath(model_path))
            if not self.model_path.exists():
                raise ValueError('Could not find model under {}'.format(self.model_path))
        self.model_dir = self.model_path.parent
        self.env_name = self.model_path.stem
        self.simulation_time = 0
        self.done = False
        self.model_debug = model_debug
        self.observations = self.__create_observations()
        self.actions = self.__create_actions()

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
            self.matlab_engine = matlab.engine.start_matlab()
            logger.info('Adding path to Matlab path: %s', self.model_dir.absolute())
            self.matlab_path = self.matlab_engine.addpath(str(self.model_dir.absolute()))
            logger.info('Creating simulation input object for model %s', self.env_name)
            self.sim_input = self.matlab_engine.Simulink.SimulationInput(self.env_name)
        else:
            self.simulation_thread = None
            self.matlab_engine = None
            self.matlab_path = None
            self.sim_input = None

    def __del__(self):
        self.close()

    def __create_observations(self):
        observations = self.define_observations()
        logger.debug('{} observation(s) defined'.format(len(observations)))
        return observations

    def define_observations(self) -> Observations:
        raise NotImplementedError

    def __create_actions(self):
        actions = self.define_actions()
        logger.debug('{} action(s) defined'.format(len(actions)))
        return actions

    def define_actions(self) -> Actions:
        raise NotImplementedError

    def calculate_reward(self):
        raise NotImplementedError

    def step(self, action):
        """
        TODO
        :param action:
        :return:
        """

        self.actions.update_current_action_index(action)
        self.send_action(self.actions.current_action_index)

        # Receive data:
        recv_data = self.recv_socket.receive()
        # When the simulation is done an empty message is sent:
        if not recv_data:
            self.observations.update_observations(None)
            reward = 0
            info = {'simulation timestamp': str(self.simulation_time)}
            self.done = True
        else:
            # Observations are everything except the last entry:
            self.observations.update_observations(recv_data[0:-1])
            reward = self.calculate_reward()
            self.simulation_time = recv_data[-1]  # simulation timestamp is last entry
            info = {'simulation timestamp': str(self.simulation_time)}
            self.done = False

        return self.observations.get_current_obs(), reward, self.done, info

    def reset(self):
        if self.simulation_thread and self.simulation_thread.is_alive():
            logger.debug('Waiting for simulation to finish')
            # Step through simulation until it is finished:
            while not self.done:
                _, _, self.done, _ = self.step(0)
            self.simulation_thread.join()
            self.stop_simulation()

        self.close_sockets()
        self.open_sockets()

        if not self.model_debug:
            # Create and start simulation thread:
            # Set initial values:
            self.set_random_initial_values()
            # Create and start simulation thread:
            logger.debug('Creating simulation thread')
            self.simulation_thread = threading.Thread(name='sim thread', target=self.matlab_engine.sim,
                                                      args=(self.sim_input,), daemon=True)
            logger.debug('Starting simulation thread')
            self.simulation_thread.start()
            logger.debug('Simulation thread started')

        # Wait for connection to be established:
        logger.debug('Waiting for connection')
        self.send_socket_thread.join()
        self.recv_socket_thread.join()
        logger.debug('Connection established')

        # Receive initial data:
        recv_data = self.recv_socket.receive()
        if recv_data:
            logger.info('Received initial data: %s' % recv_data)
            # Observations are everything except the second to last entry:
            self.observations.update_observations(recv_data[0:-1])
            self.simulation_time = recv_data[-1]  # simulation timestamp is last entry
        else:
            logger.error('No initial data received')
            self.observations.update_observations(None)

        return self.observations.get_current_obs()

    def render(self, mode='human'):
        pass

    def set_block_param(self, _block):
        if not self.model_debug:
            logger.info('Setting parameter {} of block {} to value {}'.format(_block.param, _block.path,
                                                                              str(_block.value)))
            self.sim_input = self.matlab_engine.setBlockParameter(self.sim_input, _block.path, _block.param,
                                                                  str(_block.value))

    def set_random_initial_values(self):
        # Can be implemented by subclass:
        pass

    def set_model_param(self, param, value):
        if not self.model_debug:
            logger.info('Setting model parameter {} to value {}'.format(param, str(value)))
            self.sim_input = self.matlab_engine.setModelParameter(self.sim_input, param, str(value))

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

    def send_action(self, action):
        self.send_data(action=action)

    def __send_stop_signal(self):
        self.send_data(stop=True)

    def send_data(self, stop=False, action=0):
        msg = struct.pack('<BB', int(stop), action)
        self.send_socket.send_msg(msg)

    def stop_simulation(self):
        if not self.done:
            self.__send_stop_signal()

    def num_states(self):
        return len(self.observations)

    def num_actions(self):
        return len(self.actions)

    def close(self):
        self.stop_simulation()
        logger.debug('Closing environment')
        # Close sockets:
        self.close_sockets()
        logger.info('Environment closed')
        # Close matlab engine:
        if self.matlab_engine is not None:
            self.matlab_engine.quit()


class CommSocket:

    HOST = 'localhost'

    def __init__(self, port):
        logger.debug('Setting up server on port {}'.format(port))
        self.port = port
        self.connection = None
        self.address = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, timeout=300):
        if self.is_connected():
            logger.debug('Socket already connected')
        else:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setblocking(False)
            self.server.bind((self.HOST, self.port))
            self.server.listen(1)
            logger.debug('Listening on port {}'.format(self.port))
            self.server.settimeout(timeout)
            try:
                self.connection, self.address = self.server.accept()
                logger.debug('Connection established with {}'.format(self.connection))
            except socket.timeout:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
                raise TimeoutError
            except:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()

    def receive(self):
        if self.is_connected():
            data = self.connection.recv(2048)
            data_array = array.array('d', data)
            return data_array
        else:
            logger.error('Socket not connected, nothing to receive')
            return None

    def send_msg(self, msg):
        if self.is_connected():
            self.connection.sendall(msg)
        else:
            logger.error('Socket not connected, data not sent')

    def close(self):
        if self.connection is not None:
            logger.debug('Closing connection {} at port {}'.format(self.connection, self.port))
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            self.connection = None
            self.address = None
        else:
            logger.debug('Socket not connected, nothing to close')

    def is_connected(self):
        return False if self.connection is None else True
