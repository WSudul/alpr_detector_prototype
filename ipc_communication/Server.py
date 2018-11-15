import zmq


class Server:
    def __init__(self, address, port, message_handler):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        complete_address = address + ':' + str(port)
        self._socket.bind(complete_address)
        self._message_handler = message_handler

    def bind(self, address, port):
        self._socket.bind(address, port)

    def unbind(self, address):
        self._socket.unbind(address)

    def receive_message(self):
        try:
            message = self._socket.recv_json()
            print('is message none', message is None)

            reply = self._message_handler(message)
            self._socket.send_json(reply)
        except zmq.ZMQError as e:
            print("Server Exception caught: ", e)
