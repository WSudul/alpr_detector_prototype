import zmq


class Client:

    def __init__(self, address=None, port=None, context=None):
        self._context = context if context else zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        if address is not None and port is not None:
            self.connect(address, port)

    @staticmethod
    def __create_full_address(address, port):
        return address + ':' + str(port)

    def connect(self, address, port):
        complete_address = Client.__create_full_address(address, port)
        self._socket.connect(complete_address)

    def disconnect(self, address, port):
        complete_address = Client.__create_full_address(address, port)
        self._socket.disconnect(complete_address)

    def send_message(self, message):
        reply = None
        try:
            self._socket.send_json(message)
            reply = self._socket.recv_json()
        except zmq.ZMQError as e:
            print("Client Exception caught: ", e)
        finally:
            return reply
