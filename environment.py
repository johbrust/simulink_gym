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

    def __init__(self, absolute_path, env_name):
        self.recv_socket = CommSocket(self.RECV_PORT)
        self.recv_socket_thread = threading.Thread(name='recv_socket.connect()', target=self.recv_socket.connect)
        self.recv_socket_thread.start()
        self.send_socket = CommSocket(self.SEND_PORT)
        self.send_socket_thread = threading.Thread(name='send_socket.connect()', target=self.send_socket.connect)
        self.send_socket_thread.start()
        # logging.info('Starting Matlab engine')
        # self.matlab_engine = matlab.engine.start_matlab()
        # logging.info('Adding path to Matlab path: %s' % absolute_path)
        # self.matlab_path = self.matlab_engine.addpath(absolute_path)
        # logging.info('Creating simulation input object for model %s' % env_name)
        # self.sim_info = self.matlab_engine.Simulink.SimulationInput(env_name)
        # logging.info('Creating simulation thread')
        # self.simulation_thread = threading.Thread(name='sim thread', target=self.matlab_engine.sim,
        #                                           args=(self.sim_info,), daemon=True)
        # self.simulation_started = False
        # TODO: check input value validity

    def __del__(self):
        logging.debug('Deleting Environment')
        # Wait for connection to be established:
        self.send_socket_thread.join()
        self.recv_socket_thread.join()

        # Close sockets:
        self.send_socket.close()
        self.recv_socket.close()
        logging.debug('Deleted Environment')

    def initialize_model(self, params):
        # TODO: initialize model using params:
        # self.sim_info = self.matlabEngine.setBlockParameter(self.sim_info, params.block, params.block.param,
        #                                                    str(params.block.value))
        pass

    def step(self, action):
        # TODO: implement step()
        # if not self.simulation_started:
        #     logging.info('Starting simulation thread')
        #     self.simulation_thread.start()
        #     self.simulation_started = True

        # Wait for connection to be established:
        if self.send_socket_thread.is_alive() or self.recv_socket_thread.is_alive():
            logging.info('Waiting for connection')
            self.send_socket_thread.join()
            self.recv_socket_thread.join()
            logging.info('Connection established')

        # Pass action to send socket:
        self.send_socket.send(action)

        done = False

        # TODO: Wait until data was received by receive socket
        recv_data = self.recv_socket.receive()
        # When the simulation is done an empty message is sent:
        if not recv_data:
            observation = None
            reward = 0
            done = True
        else:
            observation = recv_data[0:-1]  # observations are everything except the last entry
            reward = recv_data[-1]  # reward is last entry

        info = None

        return observation, reward, done, info

    def reset(self):
        # TODO: implement reset()
        # self.simulation_started = False
        pass

    def render(self, mode='human'):
        # TODO: implement render()
        pass


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
        logging.debug('Received data: %s' % str(data))
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
