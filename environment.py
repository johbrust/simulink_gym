import socket
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(name)s, %(levelname)s): %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')


class Environment:

    SEND_PORT = '42312'
    RECV_PORT = '42313'

    def __init__(self):
        self.sendSocket = CommSocket(self.SEND_PORT)
        self.recvSocket = CommSocket(self.RECV_PORT)

    def step(self, action):
        # TODO: implement step()

    def reset(self):
        # TODO: implement reset()


class CommSocket:

    def __init__(self, port):
        logging.info('Setting up server on port %d' % port)
        self.host = 'localhost'
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(False)
        self.server.bind(('localhost', self.port))
        self.server.listen(1)
        logging.info('Listening on port %d' % port)
        self.server.settimeout(60)
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
        return self.connection.recv(1024)

    def send(self, data):
        self.connection.sendall(data)

    def close(self):
        logging.info('Closing connection %s and port %d' % (self.connection, self.port))
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()
