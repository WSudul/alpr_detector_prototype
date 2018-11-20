from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing import Process

from detector.AlprDetector import AlprConfiguration, FRAME_SKIP
from detector.DetectorProcessWrapper import DetectorProcessArguments, DetectorArgs, AddressAndPort, \
    CommunicationConfiguration, start_detector_process
from ipc_communication.default_configuration import CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT


class DeviceLocation(Enum):
    LOCAL = 1
    NONLOCAL = 2


class DeviceStatus(Enum):
    ON = 1
    OFF = 2
    UNKNOWN = 3


class BaseDevice(ABC):
    def __init__(self, name, address, video_source) -> None:
        super().__init__()
        self.id: str = name
        self.address: str = address
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


class LocalDevice(BaseDevice):

    def __init__(self, name, address, video_source) -> None:
        super().__init__(name, address, video_source)
        self.__process: Process = None

    def get_device_type(self) -> DeviceLocation:
        return DeviceLocation.LOCAL

    def __start_detector(self):
        alpr_configuration = AlprConfiguration('eu', 'resources/openalpr.conf', 'resources/runtime_data', FRAME_SKIP)
        detector_arguments = DetectorArgs('detector1', alpr_configuration, self.video_source)
        new_process_args = DetectorProcessArguments(self.id, detector_arguments,
                                                    CommunicationConfiguration(
                                                        AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                        AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)))

        print('Starting new process with config:\n', new_process_args)
        self.__process = Process(target=start_detector_process, args=(new_process_args,))
        self.__process.start()

    def start(self) -> bool:
        if DeviceStatus.OFF == self.get_device_status():
            self.__start_detector()

        return super().start()

    def stop(self):
        if DeviceStatus.ON == self.get_device_status():
            if self.__process.is_alive():
                self.__process.terminate()
                self.__process.join()

        return super().stop()


class Device(BaseDevice):
    def get_device_type(self) -> DeviceLocation:
        return DeviceLocation.NONLOCAL
    pass
