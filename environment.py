import socket
import logging
import gym
import matlab.engine
import threading
import struct
import array

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(name)s, %(levelname)s): %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')


class Environment(gym.Env):

    SEND_PORT = 42313  # Port on which data is sent to the model
    RECV_PORT = 42312  # Port on which data is received from the model

    def __init__(self, absolute_path, env_name, initial_values, model_debug=False):
        # TODO: check input value validity
        self.simulation_thread = threading.Thread()
        self.simulation_started = False
        self.simulation_initialized = False
        self.initial_obs = initial_values
        self.initial_step = True
        self.model_debug = model_debug

        self.env_name = env_name

        # Setup connection via TCP/IP:
        self.recv_socket = CommSocket(self.RECV_PORT)
        self.recv_socket_thread = threading.Thread(name='recv_socket.connect()', target=self.recv_socket.connect)
        self.recv_socket_thread.start()
        self.send_socket = CommSocket(self.SEND_PORT)
        self.send_socket_thread = threading.Thread(name='send_socket.connect()', target=self.send_socket.connect)
        self.send_socket_thread.start()

        # Setup Matlab engine:
        if not self.model_debug:
            logging.info('Starting Matlab engine')
            self.matlab_engine = matlab.engine.start_matlab()
            logging.info('Adding path to Matlab path: %s' % absolute_path)
            self.matlab_path = self.matlab_engine.addpath(absolute_path)
            logging.info('Creating simulation input object for model %s' % self.env_name)
            self.sim_input = self.matlab_engine.Simulink.SimulationInput(self.env_name)

    def __del__(self):
        logging.debug('Deleting Environment')
        # Wait for connection to be established:
        self.send_socket_thread.join()
        self.recv_socket_thread.join()

        # Close sockets:
        self.send_socket.close()
        self.recv_socket.close()
        logging.debug('Deleted Environment')

    def initialize_simulation(self, params):
        if not self.model_debug:
            for block in params:
                # Set simulation input object:
                logging.info('Setting parameter %s of block %s to value %s' % (block.param, block.path, str(block.value)))
                self.sim_input = self.matlab_engine.setBlockParameter(self.sim_input, block.path, block.param,
                                                                      str(block.value))

            logging.info('Creating simulation thread')
            self.simulation_thread = threading.Thread(name='sim thread', target=self.matlab_engine.sim,
                                                      args=(self.sim_input,), daemon=True)
            self.simulation_started = False

        self.simulation_initialized = True

    def step(self, action):
        """
        TODO

        :param action:
        :return: observation:
                 reward:
                 done:
                 info: dictionary containing simulation timestamp
        """

        observation = None
        reward = None
        done = True
        info = None

        if self.simulation_initialized:
            if not self.model_debug:
                if not self.simulation_started:
                    logging.info('Starting simulation thread')
                    self.simulation_thread.start()
                    self.simulation_started = True

            # Wait for connection to be established:
            if self.send_socket_thread.is_alive() or self.recv_socket_thread.is_alive():
                logging.info('Waiting for connection')
                self.send_socket_thread.join()
                self.recv_socket_thread.join()
                logging.info('Connection established')

            if not self.initial_step:
                # Pass action to send socket:
                self.send_socket.send(action)
            else:
                self.initial_step = False
                logging.debug('Initial step, no action sent')

            done = False

            # TODO: Wait until data was received by receive socket
            recv_data = self.recv_socket.receive()
            logging.debug('Received data: %s' % recv_data)
            # When the simulation is done an empty message is sent:
            if not recv_data:
                observation = None
                reward = 0
                done = True
            else:
                observation = recv_data[0:-2]  # observations are everything except the last entry
                reward = recv_data[-2]  # reward is last entry
                sim_time = recv_data[-1]  # simulation timestamp

                info = {'simulation timestamp': str(sim_time)}
        else:
            # TODO: Raise error
            pass

        return observation, reward, done, info

    def reset(self):
        if self.simulation_thread.is_alive():
            logging.debug('Waiting for simulation to finish')
            self.simulation_thread.join()

        # Not working (yet), because Simulink closes the connection unilaterally after the simulation finished!
        # self.recv_socket.close()
        # self.recv_socket_thread = threading.Thread(name='recv_socket.connect()', target=self.recv_socket.connect)
        # self.recv_socket_thread.start()
        # self.send_socket.close()
        # self.send_socket_thread = threading.Thread(name='send_socket.connect()', target=self.send_socket.connect)
        # self.send_socket_thread.start()

        logging.info('Creating simulation thread')
        self.simulation_thread = threading.Thread(name='sim thread', target=self.matlab_engine.sim,
                                                  args=(self.sim_input,), daemon=True)
        self.simulation_started = False

        return self.initial_obs

    def render(self, mode='human'):
        # TODO: implement render()
        pass

    def set_block_param(self, sim_input, block):
        # TODO: Necessary?
        new_sim_input = self.matlab_engine.setBlockParameter(sim_input, block.path, block.param, str(block.value))
        return new_sim_input


class CommSocket:

    HOST = 'localhost'

    def __init__(self, port):
        logging.info('Setting up server on port %d' % port)
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(False)
        self.server.bind((self.HOST, self.port))
        self.connection = None
        self.address = None

    def connect(self, timeout=60):
        self.server.listen(1)
        logging.info('Listening on port %d' % self.port)
        self.server.settimeout(timeout)
        try:
            self.connection, self.address = self.server.accept()
            logging.info('Connection established with %s' % self.connection)
        except socket.timeout:
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            raise TimeoutError
        except:
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()

    def receive(self):
        data = self.connection.recv(2048)
        # logging.debug('Received data: %s' % str(data))
        data_array = array.array('d', data)
        return data_array

    def send(self, data):
        msg = struct.pack('<B', data)
        logging.debug('Sending message: ' + str(msg))
        self.connection.sendall(msg)

    def close(self):
        logging.info('Closing connection %s and port %d' % (self.connection, self.port))
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()
