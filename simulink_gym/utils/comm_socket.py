"""Implementation of the CommSocket class for data exchange with the Simulink model."""

import array
import socket
import struct
import threading

import numpy as np

from .. import logger


class CommSocket:
    """Class defining the sockets for communication with the Simulink simulation."""

    HOST = "localhost"

    def __init__(self, port: int, name: str = None):
        """
        Class defining the sockets for communication with the Simulink simulation.

        Parameters:
            port: int
            name: string, default: None
                optional name of the socket for debugging purposes
        """
        self._debug_prefix = f"{name}: " if name else ""
        self.port = port
        self.connection = None
        self.address = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connect_socket_thread = threading.Thread()

    def _open_socket(self, timeout=300):
        """
        Method for opening the socket and waiting for connection.

        Args:
            timeout: timeout for waiting for connection, default: 300 s

        Raises:
            TimeoutError: if the socket does not connect within the specified timeout
        """
        if self.is_connected():
            logger.info(f"{self._debug_prefix}Socket already connected")
        else:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.setblocking(True)
            self.server.bind((self.HOST, self.port))
            self.server.listen(1)
            self.server.settimeout(timeout)
            try:
                self.connection, self.address = self.server.accept()
            except socket.timeout:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
                self.connection = None
                raise TimeoutError
            except Exception:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
                self.connection = None

    def open_socket(self):
        """Method creating a thread for connecting with the simulation."""
        if not self.is_connected():
            self.connect_socket_thread = threading.Thread(
                name="socket._open_socket()", target=self._open_socket
            )
            self.connect_socket_thread.start()
        else:
            logger.error(f"{self._debug_prefix}Socket already opened or connected")

    def receive(self):
        """
        Method for receiving data from the simulation.

        Returns:
            raw data received over the socket
        """
        if self.is_connected():
            data = self.connection.recv(2048)
            data_array = array.array("d", data)
            return data_array
        else:
            logger.error(
                f"{self._debug_prefix}Socket not connected, nothing to receive"
            )
            return None

    def send_data(self, set_values: np.ndarray, stop: bool = False):
        """
        Method for sending data over the socket.

        Args:
            set_values: numpy array containing the data
            stop: flag for stopping the simulation, default: False
        """
        if self.is_connected():
            set_values = set_values.flatten()
            byte_order_str = "<d" + "d" * set_values.size
            msg = struct.pack(byte_order_str, int(stop), *set_values)
            self.connection.sendall(msg)
        else:
            logger.error(f"{self._debug_prefix}Socket not connected, data not sent")

    def close(self):
        """Method for closing the socket."""
        if self.connect_socket_thread.is_alive():
            self.connect_socket_thread.join()
            # This either times out, which causes a TimeoutError, or results in a
            # connection, which can be closed now:
        if self.connection:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
            except Exception:
                # This catches an error appearing after some time in the training
                # process. It seems that the socket used to send the data to the
                # Simulink model is closing before its close() method is called.
                # The reasons have to be investigated (#TBD).
                logger.info(
                    f"Something went wrong while closing socket "
                    f"({self.address}, {self.port})"
                )
            self.connection = None
            self.address = None
        else:
            logger.info(f"{self._debug_prefix}Socket not connected, nothing to close")

    def is_connected(self):
        """
        Check for connection of the socket.

        Returns:
            boolean indicating whether the socket is connected
        """
        return self.connection is not None and not self.connect_socket_thread.is_alive()

    def wait_for_connection(self, timeout: float = None):
        """
        Method for waiting for connection.

        Args:
            timeout: timeout for the joining of the connection thread, default: None
        """
        self.connect_socket_thread.join(timeout=timeout)
