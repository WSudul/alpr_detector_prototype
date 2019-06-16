from collections import namedtuple
from threading import Thread

import zmq

from detector.AlprDetector import create_configuration, VIDEO_SOURCE, VIDEO_SOURCE_FILE, AlprDetector, AlprDetectorArgs
from detector.ConfigRequests import DetectorRequest, ConfigurationRequest
from detector.DetectorStates import DetectorState
from ipc_communication.Client import Client
from ipc_communication.Server import AsyncServer, Server
from ipc_communication.default_configuration import CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, SERVER_PREFIX

DetectorProcessArguments = namedtuple('DetectorProcessArguments', 'name, detector_args, communication_config')

AddressAndPort = namedtuple('AddressAndPort', 'address, port')
CommunicationConfiguration = namedtuple('CommunicationConfiguration',
                                        'server, command_listener')


class DetectorManager:
    def __init__(self, name: str, detector_args: AlprDetectorArgs,
                 communication_configuration: CommunicationConfiguration):
        self.__state = DetectorState.ON
        self.__instance_name = name
        self.__role = detector_args.role
        self.__current_detector_args = detector_args
        self.__context = zmq.Context()
        self.__command_listener = AsyncServer(address=communication_configuration.command_listener.address,
                                              port=communication_configuration.command_listener.port,
                                              context=self.__context,
                                              message_handler=self.__handle_json_command)
        self.__client = Client(address=communication_configuration.server.address,
                               port=communication_configuration.server.port,
                               context=self.__context)
        self.__detector = AlprDetector(name=detector_args.instance_name, config=detector_args.alpr_configuration,
                                       video_source=detector_args.video_source,
                                       event_callback=self.__client_send_message,
                                       save_images=detector_args.capture_images,
                                       )

    def run(self):

        print('starting detector process')
        print('properties:', self.__detector.video_source_properties())
        self.__command_listener.run()

        self.__state = DetectorState.ON
        print('starting detector', '  is working now: ', self.__detector.is_working())
        while DetectorState.OFF != self.__state:
            print('State change detected in ', self.__instance_name, ' - detector working: ',
                  self.__detector.is_working())
            if DetectorState.CONFIGURE == self.__state:
                args = self.__current_detector_args
                self.__detector = AlprDetector(args.instance_name, args.alpr_configuration,
                                               args.video_source, self.__client.send_message)
                self.__state = DetectorState.ON
            elif DetectorState.ON == self.__state:
                is_successful = self.__detector.run()
                if not is_successful:
                    print('detector stopped due to invalid state - quitting run method')
                    # todo perform any needed cleanup
                    self.__state = DetectorState.OFF

    def __handle_json_command(self, json_data):
        print('handle_command ', str(json_data))
        import json
        from detector.ConfigRequests import as_command
        command = json.loads(json_data, hook=as_command)
        return self.__handle_command(command) if command else False

    def __handle_command(self, command: DetectorRequest):
        if isinstance(command, DetectorRequest):
            new_state = command.target_state()
            result = True
            if self.__state == new_state:
                print('same state encountered. No action performed')
                result = False
            elif DetectorState.CONFIGURE == new_state:

                if isinstance(command, ConfigurationRequest):
                    # reconfigure and start again
                    self.__current_detector_args = \
                        self.__update_configuration(self.__current_detector_args, **command.device_specific_config)
                    self.__state = new_state
                    self.__detector.stop()

            elif DetectorState.ON == new_state:
                # start detector
                self.__state = new_state
            elif DetectorState.OFF == new_state:
                # end detector
                self.__state = new_state
                self.__detector.stop()
            else:
                print('unknown state received: ', str(new_state))
                result = False
                # error

            return result

    @classmethod
    def __update_configuration(cls, current_config: AlprDetectorArgs, **new_kwargs):
        config_dict = current_config._asdict()
        for key, value in new_kwargs.items():
            if key in config_dict:
                config_dict[key] = value

        return AlprDetectorArgs(config_dict)

    def __client_send_message(self, message):
        message['detector_role'] = self.__role
        self.__client.send_message(message)


def start_detector_process(args: DetectorProcessArguments):
    print('starting detector process')
    import os
    print('Current working directory: ', os.getcwd())
    manager = DetectorManager(args.name, args.detector_args, args.communication_config)
    manager.run()
    print('stopping detector process')


def start_server(message_handler):
    print('starting server thread')
    ipc_server = Server(address=SERVER_PREFIX,
                        port=DEFAULT_DETECTOR_SERVER_PORT,
                        message_handler=message_handler)

    while True:
        message = ipc_server.receive_message()
        print('message received and handled: ', message)

    ipc_server.unbind(SERVER_PREFIX, str(DEFAULT_DETECTOR_SERVER_PORT))


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
    detector_arguments = AlprDetectorArgs('detector1', alpr_configuration, VIDEO_SOURCE_FILE, False, "ENTRY")
    new_process_args = DetectorProcessArguments('1', detector_arguments,
                                                CommunicationConfiguration(
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT + 1)))

    future_1 = executor.submit(start_detector_process, new_process_args)

    detector_arguments = AlprDetectorArgs('detector2', alpr_configuration, VIDEO_SOURCE, False, "ENTRY")
    # VIDEO_SOURCE)
    new_process_args = DetectorProcessArguments('2', detector_arguments,
                                                CommunicationConfiguration(
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT + 2)))
    future_2 = executor.submit(start_detector_process, new_process_args)

    detector_arguments = AlprDetectorArgs('detector3', alpr_configuration, None, False, "ENTRY")
    # using 2nd webcam
    new_process_args = DetectorProcessArguments('3', detector_arguments,
                                                CommunicationConfiguration(
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT + 3)))
    future_3 = executor.submit(start_detector_process, new_process_args)

    print(future_1.result(150))
    print(future_2.result(150))
    print(future_3.result(150))

    server_thread.join()


if __name__ == "__main__":
    main()
