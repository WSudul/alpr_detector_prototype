from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing import Process

import zmq

from detector.AlprDetector import AlprConfiguration, FRAME_SKIP
from detector.ConfigRequests import ConfigurationRequest, StateChangeRequest
from detector.DetectorManager import DetectorProcessArguments, AlprDetectorArgs, AddressAndPort, \
    CommunicationConfiguration, start_detector_process
from detector.DetectorStates import DetectorState
from ipc_communication.Client import Client
from ipc_communication.default_configuration import DEFAULT_DETECTOR_SERVER_PORT


class DeviceLocation(Enum):
    LOCAL = 1
    NONLOCAL = 2


class DeviceStatus(Enum):
    ON = 1
    OFF = 2
    UNKNOWN = 3


class DeviceRole(Enum):
    ENTRY = 1
    EXIT = 2


class BaseDevice(ABC):
    def __init__(self, name, address, listener_port, video_source, role, persistence) -> None:
        super().__init__()
        self.id = name
        self.address = address
        self.listener_port = str(listener_port)
        self.video_source = video_source
        self.status = DeviceStatus.OFF
        self.role = role
        self.persistence = persistence

    @abstractmethod
    def get_device_type(self) -> DeviceLocation:
        pass

    def get_device_status(self) -> DeviceStatus:
        return self.status

    def start(self) -> bool:
        if self.status == DeviceStatus.OFF:
            self.status = DeviceStatus.ON
            return True
        else:
            return False

    def stop(self):
        if self.status == DeviceStatus.ON:
            self.status = DeviceStatus.OFF
            return True
        else:
            return False

    @abstractmethod
    def update(self, **update_data):
        pass


class LocalDevice(BaseDevice):
    def __init__(self, name: str, video_source: str, communication_config: CommunicationConfiguration, role: DeviceRole,
                 capture_images) -> None:
        super().__init__(name, communication_config.command_listener.address,
                         communication_config.command_listener.port, video_source, role, capture_images)
        self.__process = None
        self.__communication_config = communication_config
        self.__command_sender = Client()
        self.capture_images = capture_images

    def get_device_type(self) -> DeviceLocation:
        return DeviceLocation.LOCAL

    def __start_detector(self):
        alpr_configuration = AlprConfiguration('eu', 'resources/openalpr.conf', 'resources/runtime_data', FRAME_SKIP)
        detector_arguments = AlprDetectorArgs(self.id, alpr_configuration, self.video_source, self.capture_images,
                                              self.role.name)
        new_process_args = DetectorProcessArguments(self.id, detector_arguments, self.__communication_config)

        print('Starting new process with config:\n', new_process_args)
        self.__process = Process(target=start_detector_process, args=(new_process_args,))
        self.__process.start()
        command_listener_config = new_process_args.communication_config.command_listener
        try:
            self.__command_sender.connect(command_listener_config.address, command_listener_config.port)
        except zmq.ZMQError as e:
            print('Exception thrown when connecting command sender', e, ' - ', e.errno)

    def start(self) -> bool:
        print('Starting local device')
        if DeviceStatus.OFF == self.get_device_status():
            self.__start_detector()

        return super().start()

    def stop(self):
        print('Stopping local device')
        if DeviceStatus.ON == self.get_device_status():
            stop_request = StateChangeRequest(DetectorState.OFF)
            response = self.__command_sender.send_message(stop_request)
            if self.__process.is_alive():
                self.__process.terminate()
                self.__process.join()

        return super().stop()

    def update(self, **update_data):
        if DeviceStatus.ON == self.get_device_status():
            request = ConfigurationRequest(**update_data)
            response = self.__command_sender.send_message(request)
            if response:
                if 'video_source' in update_data:
                    print('updating video_source: ', update_data.get('video_source'))
                    self.video_source = update_data.get('video_source')

                if 'address' in update_data:
                    print('updating address: ', update_data.get('address'))
                    self.address = update_data.get('address')

            return response
        else:
            return False


class RemoteDevice(BaseDevice):

    def __init__(self, name, address, listener_port, video_source, role, persistence) -> None:
        super().__init__(name, address, listener_port, video_source, role, persistence)
        self.__command_sender = Client()

    def get_device_type(self) -> DeviceLocation:
        return DeviceLocation.LOCAL

    def __start_detector(self):
        alpr_configuration = AlprConfiguration('eu', 'resources/openalpr.conf', 'resources/runtime_data', FRAME_SKIP)
        detector_arguments = AlprDetectorArgs('detector1', alpr_configuration, self.video_source, False)
        new_process_args = DetectorProcessArguments(self.id, detector_arguments,
                                                    CommunicationConfiguration(
                                                        AddressAndPort(self.address, DEFAULT_DETECTOR_SERVER_PORT),
                                                        AddressAndPort(self.address,
                                                                       self.listener_port)))

        print('Starting new process with config:\n', new_process_args)
        command_listener_config = new_process_args.communication_config.command_listener
        self.__command_sender.connect(command_listener_config.address, command_listener_config.port)
        self.__command_sender.send_message(new_process_args)

    def start(self) -> bool:
        if DeviceStatus.OFF == self.get_device_status():
            self.__start_detector()

        return super().start()

    def stop(self):
        if DeviceStatus.ON == self.get_device_status():
            stop_request = StateChangeRequest(DetectorState.OFF)
            response = self.__command_sender.send_message(stop_request)
            if response is not None and response is True:
                return super().stop()
            else:
                return False;

    def update(self, **update_data):
        if DeviceStatus.ON == self.get_device_status():
            request = ConfigurationRequest(**update_data)
            response = self.__command_sender.send_message(request)
            if response:
                if 'video_source' in update_data:
                    print('updating video_source: ', update_data.get('video_source'))
                    self.video_source = update_data.get('video_source')

                if 'address' in update_data:
                    print('updating address: ', update_data.get('address'))
                    self.address = update_data.get('address')

            return response
        else:
            return False
