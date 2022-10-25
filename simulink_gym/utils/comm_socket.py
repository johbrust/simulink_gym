import threading
import socket
from simulink_gym import logger
import array


class CommSocket:

    HOST = 'localhost'

    def __init__(self, port, name: str = None):
        self._debug_prefix = f'{name}: ' if name is not None else ''
        logger.debug(f'{self._debug_prefix}Setting up server on port {port}')
        self.port = port
        self.connection = None
        self.address = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_thread = threading.Thread()

    def _open_socket(self, timeout=300):
        if self.is_connected():
            logger.debug(f'{self._debug_prefix}Socket already connected')
        else:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.setblocking(True)
            self.server.bind((self.HOST, self.port))
            self.server.listen(1)
            logger.debug(f'{self._debug_prefix}Listening on port {self.port}')
            self.server.settimeout(timeout)
            try:
                self.connection, self.address = self.server.accept()
                logger.debug(f'{self._debug_prefix}Connection established with {self.connection}')
            except socket.timeout:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
                self.connection = None
                raise TimeoutError
            except:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
                self.connection = None

    def open_socket(self):
        if not self.is_connected():
            logger.debug(f'{self._debug_prefix}Creating and starting socket thread')
            self.socket_thread = threading.Thread(name='socket._open_socket()', target=self._open_socket)
            self.socket_thread.start()
        else:
            logger.error(f'{self._debug_prefix}Socket already opened or connected')

    def receive(self):
        #TBD: Add timeout?
        if self.is_connected():
            data = self.connection.recv(2048)
            data_array = array.array('d', data)
            return data_array
        else:
            logger.error(f'{self._debug_prefix}Socket not connected, nothing to receive')
            return None

    def send_msg(self, msg):
        if self.is_connected():
            self.connection.sendall(msg)
        else:
            logger.error(f'{self._debug_prefix}Socket not connected, data not sent')

    def close(self):
        if self.socket_thread.is_alive():
            logger.debug(f'{self._debug_prefix}Connection thread currently alive. Waiting for it to join.')
            self.socket_thread.join()
            # This either times out, which causes a TimeoutError or results in a connection,
            # which can be closed now:
        if self.connection is not None:
            logger.debug(f'{self._debug_prefix}Closing connection {self.connection} at port {self.port}')
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
            except:
                #TBD:
                # This catches an error appearing after some time in the training process. It seems
                # that the socket used to send the data to the Simulink model is closing before its
                # close() method is called. The reasons have to be investigated.
                logger.info(f"Something went wrong while closing socket ({self.address}, {self.port})")
            self.connection = None
            self.address = None
        else:
            logger.debug(f'{self._debug_prefix}Socket not connected, nothing to close')

    def is_connected(self):
        return False if ((self.connection is None) or self.socket_thread.is_alive()) else True

    def await_connection(self, timeout: float = None):
        self.socket_thread.join(timeout=timeout)
