from flask import Flask, request

from device.DeviceContainer import DeviceContainer
from ipc_communication.Server import AsyncServer
from ipc_communication.default_configuration import SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT

flask_app = Flask(__name__)


def prepare_request(message):
    # todo implement
    return message


def message_handler(message):
    print('handling message: ', message)
    post_request_data = prepare_request(message)
    # todo use when server is up
    # response = requests.post('http://localhost:8080/gate/entrance', data=post_request_data)
    # print('response: ', response.status_code)


device_container = DeviceContainer()


@flask_app.route('/')
def hello_world():
    return 'Hello World!'


@flask_app.route('/status', methods=['GET'])
def status():
    return 'Current avaiable sources: \n' + str(device_container.get_list_of_devices())


def start_detector_on_device(video_source, name, address):
    # todo implement this to connect to daemon on device and start new process there
    return None


@flask_app.route('/source', methods=['GET', 'POST'])
def manage_source():
    if request.method == 'GET':
        name = request.args.get('name')
        if name in device_container:
            source_status = device_container[name]
        else:
            source_status = 'unknown'
        return 'Source status: ' + source_status

    if request.method == 'POST':
        print('POST Request received')
        name = request.form.get('name')
        new_status = request.form.get('status')

        if name not in device_container:
            print('Starting new detector process')
            video_source = request.form.get('video_source')
            location = request.form.get('location')
            address = request.form.get('address')

            device_container.add_device(name, location, address)
            if 'ON' == new_status:
                device_container.start_device(name)

            if 'LOCAL' == location:
                start_detector(video_source, name)
            elif 'NONLOCAL' == location:
                start_detector_on_device(video_source, name, address)

            return 'added device'
        else:
            # todo handle update
            if 'ON' == new_status:
                return device_container.start_device(name)
            elif 'OFF' == new_status:
                return device_container.stop_device(name)


if __name__ == '__main__':
    print('starting ipc server')
    ipc_server = AsyncServer(SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, message_handler)
    ipc_server.run()

    print('Starting flask_app')
    flask_app.run()
