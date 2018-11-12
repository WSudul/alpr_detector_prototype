import zmq


class Server:
    def __init__(self, address, port, message_handler):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.bind(address + ':' + port)
        self._message_handler = message_handler

    def bind(self, address, port):
        self._socket.bind(address, port)

    def unbind(self, address):
        self._socket.unbind(address)

    def receive_message(self, message):
        reply = None
        try:
            message = self._socket.recv_json(message)
            reply = self._message_handler(message)
            self._socket.recv_json(reply)
        except zmq.ZMQError as e:
            print("Exception caught: ", e)
        finally:
            return reply
