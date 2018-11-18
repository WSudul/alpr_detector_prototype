from threading import Thread

import zmq


class Server:
    def __init__(self, address, port, message_handler):
        self._context = zmq.Context()
        self._context.setsockopt(zmq.ZMQ_LINGER, 100)
        self._socket = self._context.socket(zmq.REP)
        self.__address = address
        self.__port = port
        self._message_handler = message_handler

    @classmethod
    def __create_full_address(cls, address, port):
        return address + ':' + str(port)

    def bind(self, address, port):
        self._socket.bind(address, port)

    def unbind(self, address, port):
        self._socket.unbind(Server.__create_full_address(address, port))

    def receive_message(self):
        try:
            message = self._socket.recv_json()
            if message is None:
                print('Received message is None')

            reply = self._message_handler(message)
            self._socket.send_json(reply)
        except zmq.ZMQError as e:
            print("Server Exception caught: ", e)


class AsyncServer(Server):
    def __init__(self, address, port, message_handler):
        super().__init__(address, port, message_handler)
        self.__run = False

    def __run_in_loop(self):
        while self.__run:
            self.receive_message()

    def run(self):
        self.bind(self.__address, self.__port)
        if self.__run is not True:
            self.__run = True
            server_thread = Thread(target=self.__run_in_loop)
            server_thread.start()
            server_thread.join()

    def stop(self):
        self._socket.unbind()
        self.__run = False
