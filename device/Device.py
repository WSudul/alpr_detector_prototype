from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing import Process

from detector.AlprDetector import AlprConfiguration, FRAME_SKIP
from detector.ConfigRequests import ConfigurationRequest, StateChangeRequest, DetectorState
from detector.DetectorProcessWrapper import DetectorProcessArguments, AlprDetectorArgs, AddressAndPort, \
    CommunicationConfiguration, start_detector_process
from ipc_communication.Client import Client
from ipc_communication.default_configuration import DEFAULT_DETECTOR_SERVER_PORT


class DeviceLocation(Enum):
    LOCAL = 1
    NONLOCAL = 2


class DeviceStatus(Enum):
    ON = 1
    OFF = 2
    UNKNOWN = 3


class BaseDevice(ABC):
    def __init__(self, name, address, listener_port, video_source) -> None:
        super().__init__()
        self.id: str = name
        self.address: str = address
        self.listener_port: str = str(listener_port)
        self.video_source: str = video_source
        self.status: DeviceStatus = DeviceStatus.OFF

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

    def __init__(self, name, address, listener_port, video_source) -> None:
        super().__init__(name, address, listener_port, video_source)
        self.__process: Process = None
        self.__command_sender: Client = Client()

    def get_device_type(self) -> DeviceLocation:
        return DeviceLocation.LOCAL

    def __start_detector(self):
        alpr_configuration = AlprConfiguration('eu', 'resources/openalpr.conf', 'resources/runtime_data', FRAME_SKIP)
        detector_arguments = AlprDetectorArgs('detector1', alpr_configuration, self.video_source)
        new_process_args = DetectorProcessArguments(self.id, detector_arguments,
                                                    CommunicationConfiguration(
                                                        AddressAndPort(self.address, DEFAULT_DETECTOR_SERVER_PORT),
                                                        AddressAndPort(self.address,
                                                                       self.listener_port)))

        print('Starting new process with config:\n', new_process_args)
        self.__process = Process(target=start_detector_process, args=(new_process_args,))
        self.__process.start()
        command_listener_config = new_process_args.communication_config.command_listener
        self.__command_sender.connect(command_listener_config.address, command_listener_config.port)

    def start(self) -> bool:
        if DeviceStatus.OFF == self.get_device_status():
            self.__start_detector()

        return super().start()

    def stop(self):
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
