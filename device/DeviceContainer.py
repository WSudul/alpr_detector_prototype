from collections import namedtuple

from detector.DetectorManager import CommunicationConfiguration, AddressAndPort
from device.Device import DeviceLocation, LocalDevice, DeviceStatus, RemoteDevice, DeviceRole
from ipc_communication.default_configuration import DEFAULT_DETECTOR_SERVER_PORT, CLIENT_PREFIX


class DeviceContainer:
    def __init__(self) -> None:
        super().__init__()
        self.__devices = dict()

    def __contains__(self, item):
        return item in self.__devices

    def add_device(self, name: str, device_type: DeviceLocation, address: str, listener_port,
                   video_source: str, role: DeviceRole, capture_images: bool) -> bool:
        if name in self.__devices:
            return False

        if device_type is DeviceLocation.LOCAL:
            print('adding local device ', name)
            config = CommunicationConfiguration(server=
                                                AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                command_listener=
                                                AddressAndPort(address,
                                                               listener_port))

            new_device = LocalDevice(name=name, video_source=video_source, communication_config=config,
                                     capture_images=capture_images, role=role)
            self.__devices[name] = new_device
        else:
            print('adding remote device ', name)
            new_device = RemoteDevice(name=name, address=address, listener_port=listener_port,
                                      video_source=video_source, role=role, persistence=capture_images)
            self.__devices[name] = new_device

        return True

    def remove_device(self, name: str) -> None:
        del self.__devices[name]

    def get_list_of_devices(self):
        return self.__devices.keys()

    def get_device_status(self, name: str):
        device = self.__devices.get(name, None)
        return None if device is None else device.status

    def get_device_location(self, name: str):
        device = self.__devices.get(name, None)
        return None if device is None else device.get_device_type()

    def get_device_address(self, name: str):
        device = self.__devices.get(name, None)
        return None if device is None else (device.address + ':' + device.listener_port)

    def start_device(self, name: str) -> bool:
        device = self.__devices.get(name, None)
        return False if device is None else device.start()

    def stop_device(self, name: str) -> bool:
        device = self.__devices.get(name, None)
        return False if device is None else device.stop()

    def handle_device_update(self, name, new_status: DeviceStatus, address=None,
                             listener_port=None, video_source: str = None, capture_images=None) -> bool:
        device = self.__devices.get(name, None)
        if device is None:
            return False

        if DeviceStatus.ON == new_status:

            if video_source:
                args = dict()
                if video_source:
                    args['video_source'] = video_source
                if address:
                    args['address'] = address
                if listener_port:
                    args['listener_port'] = listener_port
                if capture_images:
                    args['capture_images'] = capture_images

                result = device.update(args)
                return result

            return device.start()
        elif DeviceStatus.OFF == new_status:
            return device.stop()
        else:
            print('Incorrect device status passed to update')
            return False

    DeviceSnapshot = namedtuple('DeviceSnapshot', 'name, status, address, location,gate,persistence')

    def get_devices_snapshot(self):
        names = self.get_list_of_devices()
        snapshot = list()
        for name in names:
            status = self.get_device_status(name)
            address = self.get_device_address(name)
            location = self.get_device_location(name)
            gate = self.getdevice_role(name)
            persistence = self.getdevice_persistence(name)
            snapshot.append(DeviceContainer.DeviceSnapshot(name, status, address, location, gate, persistence))
        return snapshot

    def getdevice_role(self, name):
        device = self.__devices.get(name, None)
        return None if device is None else device.role

    def getdevice_persistence(self, name):
        device = self.__devices.get(name, None)
        return None if device is None else device.persistence
