from abc import abstractmethod, ABC
from enum import Enum


class DetectorState(Enum):
    ON = 0,
    CONFIGURE = 1
    OFF = 2


class DetectorRequest(ABC):
    @abstractmethod
    def target_state(self) -> DetectorState:
        pass


class StateChangeRequest(DetectorRequest):
    def __init__(self, state):
        self.target_state = state

    def target_state(self) -> DetectorState:
        return self.target_state


class ConfigurationRequest(DetectorRequest):
    def __init__(self, **kwargs):
        self.target_state = DetectorState.CONFIGURE
        self.device_specific_config = kwargs

    def target_state(self) -> DetectorState:
        return self.target_state


def as_command(data_dict: dict):
    if 'target_state' not in data_dict:
        return None
    import json
    if 'device_specific_config' in data_dict:
        config_dict: dict = json.loads(data_dict['device_specific_config'])
        return ConfigurationRequest(**config_dict)
    else:

        return StateChangeRequest(json.loads(data_dict['target_state']))
