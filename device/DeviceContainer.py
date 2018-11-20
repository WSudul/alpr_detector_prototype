from device.BaseDevice import DeviceLocation, LocalDevice, Device


class DeviceContainer:
    def __init__(self) -> None:
        super().__init__()
        self.__devices = dict()

    def add_device(self, name: str, device_type: DeviceLocation, address: str, video_source: str) -> bool:
        if name in self.__devices:
            return False

        new_device = LocalDevice(name, address, video_source) \
            if DeviceLocation.LOCAL == device_type else Device(name, address, video_source)

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
        return None if device is None else device.location

    def get_device_address(self, name: str):
        device = self.__devices.get(name, None)
        return None if device is None else device.address

    def start_device(self, name: str) -> bool:
        device = self.__devices.get(name, None)
        return False if device is None else device.start()

    def stop_device(self, name: str) -> bool:
        device = self.__devices.get(name, None)
        return False if device is None else device.stop()
