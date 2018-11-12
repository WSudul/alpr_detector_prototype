import zmq


class Client():

    def __init__(self, address=None, port=None):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        if address is not None and port is not None:
            self.connect(address, port)

    def connect(self, address, port):
        self._socket.connect(address, port)

    def disconnect(self, address, port):
        self._socket.disconnect(address)

    def send_message(self, message):
        reply = None
        try:
            self._socket.send_json(message)
            reply = self._socket.recv_json()
        except zmq.ZMQError as e:
            print("Exception caught: ", e)
        finally:
            return reply
