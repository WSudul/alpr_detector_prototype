from enum import Enum


class DeviceLocation(Enum):
    LOCAL = 1
    NONLOCAL = 2


class DeviceStatus(Enum):
    ON = 1
    OFF = 2
    UNKNOWN = 3


class Device:
    def __init__(self, name, device_type, address) -> None:
        super().__init__()
        self.id: str = name
        self.type: DeviceLocation = device_type
        self.address: str = address
        self.status: DeviceStatus = DeviceStatus.OFF

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
