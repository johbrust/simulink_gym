import socket
import logging
import gym
import matlab.engine
import threading
import struct
import array
from collections import namedtuple

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(name)s, %(levelname)s): %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

block = namedtuple('block', ['path', 'param', 'value'])


class Environment(gym.Env):

    SEND_PORT = 42313  # Port on which data is sent to the model
    RECV_PORT = 42312  # Port on which data is received from the model

    def __init__(self, absolute_path, env_name, model_debug=False):
        # TODO: check input value validity
        self.model_debug = model_debug
        self.env_name = env_name
        self.simulation_time = 0

        # Create TCP/IP sockets and empty threads:
        self.recv_socket = CommSocket(self.RECV_PORT)
        self.recv_socket_thread = threading.Thread()
        self.send_socket = CommSocket(self.SEND_PORT)
        self.send_socket_thread = threading.Thread()

        # Create empty simulation thread:
        self.simulation_thread = threading.Thread()

        # Setup Matlab engine:
        if not self.model_debug:
            logging.debug('Starting Matlab engine')
            self.matlab_engine = matlab.engine.start_matlab()
            logging.debug('Adding path to Matlab path: %s' % absolute_path)
            self.matlab_path = self.matlab_engine.addpath(absolute_path)
            logging.debug('Creating simulation input object for model %s' % self.env_name)
            self.sim_input = self.matlab_engine.Simulink.SimulationInput(self.env_name)

    def __del__(self):
        logging.debug('Deleting Environment')
        # Close sockets:
        self.close_sockets()
        logging.debug('Deleted Environment')
        # Close matlab engine:
        self.matlab_engine.quit()

    def step(self, action):
        """
        TODO

        :param action:
        :return: observation:
                 reward:
                 done:
                 info: dictionary containing simulation timestamp
        """

        self.send_socket.send(action)

        # Receive data:
        recv_data = self.recv_socket.receive()
        logging.debug('Received data: %s' % recv_data)
        # When the simulation is done an empty message is sent:
        if not recv_data:
            observation = None
            reward = 0
            info = {'simulation timestamp': str(self.simulation_time)}
            done = True
        else:
            observation = recv_data[0:-2]  # observations are everything except the second to last entry
            reward = recv_data[-2]  # reward is second to last entry
            self.simulation_time = recv_data[-1]  # simulation timestamp is last entry
            info = {'simulation timestamp': str(self.simulation_time)}
            done = False

        # TODO: observation as np.array?
        return observation, reward, done, info

    def reset(self):
        if not self.model_debug and self.simulation_thread.is_alive():
            logging.info('Waiting for simulation to finish')
            # Step through simulation until it is finished:
            done = False
            while not done:
                _, _, done, _ = self.step(0)
            self.simulation_thread.join()
            # Stopping does not work yet:
            # self.stop_simulation()

        self.close_sockets()
        self.open_sockets()

        # Create and start simulation thread:
        if not self.model_debug:
            # Create and start simulation thread:
            logging.debug('Creating simulation thread')
            self.simulation_thread = threading.Thread(name='sim thread', target=self.matlab_engine.sim,
                                                      args=(self.sim_input,), daemon=True)
            logging.debug('Starting simulation thread')
            self.simulation_thread.start()
            logging.debug('Simulation thread started')

        # Wait for connection to be established:
        logging.debug('Waiting for connection')
        self.send_socket_thread.join()
        self.recv_socket_thread.join()
        logging.debug('Connection established')

        # Receive initial data:
        recv_data = self.recv_socket.receive()
        if recv_data:
            logging.debug('Received initial data: %s' % recv_data)
            observation = recv_data[0:-2]  # observations are everything except the second to last entry
            self.simulation_time = recv_data[-1]  # simulation timestamp is last entry
        else:
            logging.error('No initial data received')
            observation = None

        # TODO: observation as np.array?
        return observation

    def render(self, mode='human'):
        # TODO: implement render()
        pass

    def set_block_param(self, _block):
        if not self.model_debug:
            logging.info('Setting parameter %s of block %s to value %s' % (_block.param, _block.path, str(_block.value)))
            self.sim_input = self.matlab_engine.setBlockParameter(self.sim_input, _block.path, _block.param,
                                                                  str(_block.value))

    def open_sockets(self):
        if self.recv_socket_thread.is_alive():
            logging.debug('recv_socket_thread already running')
        else:
            if self.recv_socket.is_connected():
                logging.debug('recv_socket still connected, closing socket')
                self.recv_socket.close()
            logging.debug('Creating and starting recv_socket thread')
            self.recv_socket_thread = threading.Thread(name='recv_socket.connect()', target=self.recv_socket.connect,
                                                       daemon=True)
            self.recv_socket_thread.start()

        if self.send_socket_thread.is_alive():
            logging.debug('send_socket_thread already running')
        else:
            if self.send_socket.is_connected():
                logging.debug('send_socket still connected, closing socket')
                self.send_socket.close()
            logging.debug('Creating and starting send_socket thread')
            self.send_socket_thread = threading.Thread(name='send_socket.connect()', target=self.send_socket.connect,
                                                       daemon=True)
            self.send_socket_thread.start()

    def close_sockets(self):
        if self.recv_socket_thread.is_alive():
            self.recv_socket_thread.join()
        self.recv_socket.close()
        if self.send_socket_thread.is_alive():
            self.send_socket_thread.join()
        self.send_socket.close()

    def stop_simulation(self):
        # The following code does not work. Another solution has to be found!
        # if not self.model_debug:
        #     logging.debug('Stopping simulation')
        #     current_simulation = self.matlab_engine.gcs
        #     self.matlab_engine.set_param(current_simulation, 'SimulationCommand', 'stop')
        #     logging.debug('Simulation stopped')
        pass


class CommSocket:

    HOST = 'localhost'

    def __init__(self, port):
        logging.debug('Setting up server on port %d' % port)
        self.port = port
        self.connection = None
        self.address = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, timeout=60):
        if self.is_connected():
            logging.info('Socket already connected')
        else:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setblocking(False)
            self.server.bind((self.HOST, self.port))
            self.server.listen(1)
            logging.debug('Listening on port %d' % self.port)
            self.server.settimeout(timeout)
            try:
                self.connection, self.address = self.server.accept()
                logging.debug('Connection established with %s' % self.connection)
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
            # logging.debug('Received data: %s' % str(data))
            data_array = array.array('d', data)
            return data_array
        else:
            logging.error('Socket not connected, nothing to receive')
            return None

    def send(self, data):
        if self.is_connected():
            msg = struct.pack('<B', data)
            logging.debug('Sending message: ' + str(msg))
            self.connection.sendall(msg)
        else:
            logging.error('Socket not connected, data not sent')

    def close(self):
        if self.connection is not None:
            logging.debug('Closing connection %s at port %d' % (self.connection, self.port))
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            self.connection = None
            self.address = None
        else:
            logging.debug('Socket not connected, nothing to close')

    def is_connected(self):
        return False if self.connection is None else True
