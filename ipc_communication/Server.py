from threading import Thread

import zmq


class Server:
    def __init__(self, address, port, message_handler):
        self._context = zmq.Context()
        # self._context.setsockopt(zmq.ZMQ_LINGER, 100)
        self.__socket = self._context.socket(zmq.REP)
        self.__address = address
        self.__port = port
        self.__message_handler = message_handler

    @classmethod
    def __create_full_address(cls, address, port):
        return address + ':' + str(port)

    def bind(self, address, port):
        self.__socket.bind(Server.__create_full_address(address, port))

    def unbind(self, address, port):
        self.__socket.unbind(Server.__create_full_address(address, port))

    def receive_message(self):
        try:
            message = self.__socket.recv_json()
            if message is None:
                print('Received message is None')

            reply = self.__message_handler(message)
            self.__socket.send_json(reply)
        except zmq.ZMQError as e:
            print("Server Exception caught: ", e)


class AsyncServer(Server):
    def __init__(self, address, port, message_handler):
        Server.__init__(self, address, port, message_handler)
        self.__run = False
        self.__server_thread: Thread = None

    def __run_in_loop(self):
        while self.__run:
            self.receive_message()

    def run(self):
        self.bind(self._Server__address, self._Server__port)
        if self.__run is not True:
            self.__run = True
            self.__server_thread = Thread(target=self.__run_in_loop)
            self.__server_thread.start()

    def stop(self):
        self.__socket.unbind()
        self.__server_thread.join()
        self.__run = False
