import socket
import logging
import gym
import matlab.engine
import threading
import struct
import array
from collections import namedtuple
from observation import Observations
from action import Actions


block = namedtuple('block', ['path', 'param', 'value'])


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s (%(threadName)s, %(levelname)s), (%(funcName)s: %(lineno)d): %('
                                  'message)s',
                              datefmt='%d-%b-%y %H:%M:%S')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class Environment(gym.Env):

    SEND_PORT = 42313  # Port on which data is sent to the model
    RECV_PORT = 42312  # Port on which data is received from the model

    def __init__(self, absolute_path, env_name, model_debug=False):
        # TODO: check input value validity
        self.model_debug = model_debug
        self.env_name = env_name
        self.simulation_time = 0
        self.done = False
        self.observations = self.define_observations()
        self.actions = self.define_actions()

        # Create TCP/IP sockets and empty threads:
        self.recv_socket = CommSocket(self.RECV_PORT)
        self.recv_socket_thread = threading.Thread()
        self.send_socket = CommSocket(self.SEND_PORT)
        self.send_socket_thread = threading.Thread()

        # Create empty simulation thread:
        self.simulation_thread = threading.Thread()

        # Setup Matlab engine:
        if not self.model_debug:
            logger.info('Starting Matlab engine')
            self.matlab_engine = matlab.engine.start_matlab()
            logger.info('Adding path to Matlab path: %s' % absolute_path)
            self.matlab_path = self.matlab_engine.addpath(absolute_path)
            logger.info('Creating simulation input object for model %s' % self.env_name)
            self.sim_input = self.matlab_engine.Simulink.SimulationInput(self.env_name)

    def define_observations(self) -> Observations:
        raise NotImplementedError

    def define_actions(self) -> Actions:
        raise NotImplementedError

    def calculate_reward(self):
        raise NotImplementedError

    def __del__(self):
        logger.info('Deleting Environment')
        # Close sockets:
        self.close_sockets()
        logger.info('Deleted Environment')
        # Close matlab engine:
        self.matlab_engine.quit()

    def step(self, action):
        """
        TODO
        :param action:
        :return:
        """

        self.actions.update_current_action_index(action)
        self.send_socket.send(self.actions.current_action_index)

        # Receive data:
        recv_data = self.recv_socket.receive()
        # When the simulation is done an empty message is sent:
        if not recv_data:
            self.observations.update_observations(None)
            reward = 0
            info = {'simulation timestamp': str(self.simulation_time)}
            self.done = True
        else:
            # Observations are everything except the second to last entry:
            self.observations.update_observations(recv_data[0:-1])
            reward = self.calculate_reward()
            self.simulation_time = recv_data[-1]  # simulation timestamp is last entry
            info = {'simulation timestamp': str(self.simulation_time)}
            self.done = False

        return self.observations.get_current_obs_nparray(), reward, self.done, info

    def reset(self):
        if not self.model_debug and self.simulation_thread.is_alive():
            logger.debug('Waiting for simulation to finish')
            # Step through simulation until it is finished:
            while not self.done:
                _, _, self.done, _ = self.step(0)
            self.simulation_thread.join()
            # Stopping does not work yet:
            # self.stop_simulation()

        self.close_sockets()
        self.open_sockets()

        # Create and start simulation thread:
        if not self.model_debug:
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
            logger.debug('Received initial data: %s' % recv_data)
            # Observations are everything except the second to last entry:
            self.observations.update_observations(recv_data[0:-1])
            self.simulation_time = recv_data[-1]  # simulation timestamp is last entry
        else:
            logger.error('No initial data received')
            self.observations.update_observations(None)

        return self.observations.get_current_obs_nparray()

    def render(self, mode='human'):
        # TODO: implement render()
        pass

    def set_block_param(self, _block):
        if not self.model_debug:
            logger.info('Setting parameter %s of block %s to value %s' % (_block.param, _block.path, str(_block.value)))
            self.sim_input = self.matlab_engine.setBlockParameter(self.sim_input, _block.path, _block.param,
                                                                  str(_block.value))

    def set_random_initial_values(self):
        # Can be implemented by subclass:
        pass

    def set_model_param(self, param, value):
        if not self.model_debug:
            logger.info('Setting model parameter %s to value %s' % (param, str(value)))
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

    def stop_simulation(self):
        # The following code does not work. Another solution has to be found!
        # if not self.model_debug:
        #     logger.debug('Stopping simulation')
        #     current_simulation = self.matlab_engine.gcs
        #     self.matlab_engine.set_param(current_simulation, 'SimulationCommand', 'stop')
        #     logger.debug('Simulation stopped')
        pass

    def num_states(self):
        return len(self.observations)

    def num_actions(self):
        return len(self.actions)


class CommSocket:

    HOST = 'localhost'

    def __init__(self, port):
        logger.debug('Setting up server on port %d' % port)
        self.port = port
        self.connection = None
        self.address = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, timeout=300):
        if self.is_connected():
            logger.info('Socket already connected')
        else:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setblocking(False)
            self.server.bind((self.HOST, self.port))
            self.server.listen(1)
            logger.debug('Listening on port %d' % self.port)
            self.server.settimeout(timeout)
            try:
                self.connection, self.address = self.server.accept()
                logger.debug('Connection established with %s' % self.connection)
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
            # logger.debug('Received data: %s' % str(data))
            data_array = array.array('d', data)
            return data_array
        else:
            logger.error('Socket not connected, nothing to receive')
            return None

    def send(self, data):
        if self.is_connected():
            msg = struct.pack('<B', data)
            # logger.debug('Sending message: ' + str(msg))
            self.connection.sendall(msg)
        else:
            logger.error('Socket not connected, data not sent')

    def close(self):
        if self.connection is not None:
            logger.debug('Closing connection %s at port %d' % (self.connection, self.port))
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
