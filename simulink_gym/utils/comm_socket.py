import threading
import socket
from .. import logger
import array
import numpy as np
import struct


class CommSocket:
    """Class defining the sockets necessary for communication with the Simulink
    simulation.
    """

    HOST = "localhost"

    def __init__(self, port: int, name: str = None):
        """Class defining the sockets necessary for communication with the Simulink
        simulation.

        Parameters:
            port: int
            name: string, default: None
                optional name of the socket for debugging purposes
        """
        self._debug_prefix = f"{name}: " if name is not None else ""
        self.port = port
        self.connection = None
        self.address = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_thread = threading.Thread()

    def _open_socket(self, timeout=300):
        """Method for opening the socket and waiting for connection.

        Parameters:
            timeout, default: 300 s
                timeout for waiting for connection
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
            self.socket_thread = threading.Thread(
                name="socket._open_socket()", target=self._open_socket
            )
            self.socket_thread.start()
        else:
            logger.error(f"{self._debug_prefix}Socket already opened or connected")

    def receive(self):
        """Method for receiving data from the simulation.

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
        """Method for sending data over the socket.

        Parameters:
            set_values: numpy.ndarray
                numpy array containing the data
            stop: bool, default: False
                flag for stopping the simulation
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
        if self.socket_thread.is_alive():
            self.socket_thread.join()
            # This either times out, which causes a TimeoutError, or results in a
            # connection, which can be closed now:
        if self.connection is not None:
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
        """Check for connection of the socket."""
        return (
            False
            if ((self.connection is None) or self.socket_thread.is_alive())
            else True
        )

    def wait_for_connection(self, timeout: float = None):
        """Method for waiting for connection.

        Parameters:
            timeout: float, default: None
                timeout for the joining of the connection thread
        """
        self.socket_thread.join(timeout=timeout)
