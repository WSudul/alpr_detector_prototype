from collections import namedtuple
from threading import Thread

import zmq

AddressAndPort = namedtuple('AddressAndPort', 'address, port')
FullAddressAndHandler = namedtuple('FullAddressAndHandler', 'address, callback')


class Server:
    def __init__(self, message_handler, address=None, port=None, context=None):
        self._context = context if context else zmq.Context()
        self.__sockets = dict()  # dict of {socket: {Address and Handler}}

        self.__default_message_handler = message_handler
        self.__poller = zmq.Poller()

        if address is not None and port is not None:
            self.bind(address, port, message_handler)

    @staticmethod
    def __create_full_address(address, port):
        print(address, ' : ', port)
        return address + ':' + str(port)

    def bind(self, address, port, handler=None):
        full_address = Server.__create_full_address(address, port)

        existing_addresses = list(i.address for i in self.__sockets.values())

        if full_address in existing_addresses:
            print('Socket was already bound to ', full_address)
            return

        socket = self._context.socket(zmq.REP)
        socket.bind(full_address)

        if handler is None:
            handler = self.__default_message_handler

        self.__sockets[socket] = FullAddressAndHandler(full_address, handler)
        self.__poller.register(socket, zmq.POLLIN)

    def unbind(self, address, port):
        full_address = Server.__create_full_address(address, port)

        address_socket_dict = {v.address: k for k, v in self.__sockets.items()}
        socket = address_socket_dict.get(full_address, None)

        popped_socket: zmq.Socket = self.__sockets.pop(socket, None)
        if popped_socket is None:
            print('No socket was bound to ', full_address)
            return

        popped_socket.unbind(full_address)
        self.__poller.unregister(popped_socket)
        self.__sockets.pop(full_address)

    def receive_message(self):
        try:
            events = dict(self.__poller.poll(timeout=1000))

            for event in events:
                socket_data: FullAddressAndHandler = self.__sockets[event]

                message = event.recv_json()
                if message is None:
                    print('Received message is None')

                reply = socket_data.callback(message)
                event.send_json(reply)

        except zmq.ZMQError as e:
            print("Server Exception caught: ", e)


class AsyncServer(Server):
    def __init__(self, message_handler, address=None, port=None, context=None):
        Server.__init__(self,
                        address=address,
                        port=port,
                        context=context,
                        message_handler=message_handler)
        self.__run = False
        self.__server_thread: Thread = None

    def __run_in_loop(self):
        while self.__run:
            self.receive_message()

    def run(self):
        if self.__run is not True:
            self.__run = True
            self.__server_thread = Thread(target=self.__run_in_loop)
            self.__server_thread.start()

    def stop(self):
        self.__sockets.unbind()
        self.__server_thread.join()
        self.__run = False
