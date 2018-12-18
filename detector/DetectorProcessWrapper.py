from collections import namedtuple
from threading import Thread

import zmq

from detector.AlprDetector import create_configuration, VIDEO_SOURCE, VIDEO_SOURCE_FILE, AlprDetector, AlprDetectorArgs
from detector.ConfigRequests import DetectorRequest, ConfigurationRequest, DetectorState
from ipc_communication.Client import Client
from ipc_communication.Server import AsyncServer, Server
from ipc_communication.default_configuration import CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, SERVER_PREFIX

DetectorProcessArguments = namedtuple('DetectorProcessArguments', 'name, detector_args, communication_config')

AddressAndPort = namedtuple('AddressAndPort', 'address, port')
CommunicationConfiguration = namedtuple('CommunicationConfiguration',
                                        'server_full_address, command_listener_full_address')
DetectorProcessArguments = namedtuple('DetectorProcessArguments', 'name, detector_args, communication_config')


class DetectorManager:
    def __init__(self, name: str, detector_args: DetectorArgs, communication_configuration: CommunicationConfiguration):
        self.__instance_name = name
        self.__client = Client(communication_configuration.server_full_address.address,
                               communication_configuration.server_full_address.port)
        self.__detector = AlprDetector(detector_args.instance_name, detector_args.alpr_configuration,
                                       detector_args.video_source,
                                       self.__client.send_message)
        # todo add communication to stop/start detection - xmlrpc from standard lib?

    def run(self):
        print('starting detector process')
        print('properties\n:', self.__detector.video_source_properties())
        detector_thread = Thread(target=run_detector_wrapper, args=[self.__detector], daemon=True)
        detector_thread.start()
        print('starting detector', '  is working now: ', self.__detector.is_working())

        detector_thread.join()


def run_detector_wrapper(detector):
    detector.run()


def start_detector_process(args: DetectorProcessArguments):
    print('starting detector process')
    manager = DetectorManager(args.name, args.detector_args, args.communication_config)
    manager.run()
    print('stopping detector process')


def start_server(message_handler):
    print('starting server thread')
    ipc_server = Server(SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, message_handler)

    while True:
        ipc_server.receive_message()
        print('message received and handled')

    ipc_server.unbind(SERVER_PREFIX + ':' + str(DEFAULT_DETECTOR_SERVER_PORT))


def message_handler_callback(message):
    print('message_handler_callback')
    print(message)
    response = True
    return response


def main():
    server_thread = Thread(target=start_server, args=[message_handler_callback])
    server_thread.start()

    from concurrent.futures import ProcessPoolExecutor
    executor = ProcessPoolExecutor(max_workers=3)

    alpr_configuration = create_configuration()
    detector_arguments = DetectorArgs('detector1', alpr_configuration, VIDEO_SOURCE_FILE)
    new_process_args = DetectorProcessArguments('1', detector_arguments,
                                                CommunicationConfiguration(
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)))
    future_1 = executor.submit(start_detector_process, new_process_args)

    detector_arguments = DetectorArgs('detector2', alpr_configuration, VIDEO_SOURCE)  # VIDEO_SOURCE)
    new_process_args = DetectorProcessArguments('2', detector_arguments,
                                                CommunicationConfiguration(
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)))
    future_2 = executor.submit(start_detector_process, new_process_args)

    detector_arguments = DetectorArgs('detector3', alpr_configuration, None)  # using 2nd webcam
    new_process_args = DetectorProcessArguments('3', detector_arguments,
                                                CommunicationConfiguration(
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)))
    future_3 = executor.submit(start_detector_process, new_process_args)

    print(future_1.result(150))
    print(future_2.result(150))
    print(future_3.result(150))

    server_thread.join()


if __name__ == "__main__":
    main()
