import zmq


class Client:

    def __init__(self, address=None, port=None, context=None):
        self.__context = context if context else zmq.Context()
        self.__socket = self.__context.socket(zmq.REQ)
        self.__socket.setsockopt(zmq.RCVTIMEO, 10000)
        if address is not None and port is not None:
            self.connect(address, port)

    @staticmethod
    def __create_full_address(address, port):
        return address + ':' + str(port)

    def connect(self, address, port):
        complete_address = Client.__create_full_address(address, port)
        print('Connecting to :', complete_address)
        self.__socket.connect(complete_address)

    def disconnect(self, address, port):
        complete_address = Client.__create_full_address(address, port)
        self.__socket.disconnect(complete_address)

    def send_message(self, message):
        print('send_message', message)
        reply = None
        try:
            self.__socket.send_json(message)
            reply = self.__socket.recv_json()
        except zmq.ZMQError as e:
            print("Client Exception caught: ", e)
        finally:
            return reply
