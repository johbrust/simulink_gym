import socket
from simulink_gym import logger
import array

class CommSocket:

    HOST = 'localhost'

    def __init__(self, port):
        logger.debug('Setting up server on port {}'.format(port))
        self.port = port
        self.connection = None
        self.address = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self, timeout=300):
        if self.is_connected():
            logger.debug('Socket already connected')
        else:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.setblocking(True)
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
        #TBD: Add timeout?
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
