from abc import ABC, abstractmethod

import zmq

DEFAULT_DETECTOR_SERVER_PORT = 8888
TCP_PROTOCOL = 'tcp'
CLIENT_PREFIX = 'tcp://localhost'
SERVER_PREFIX = 'tcp://*'
