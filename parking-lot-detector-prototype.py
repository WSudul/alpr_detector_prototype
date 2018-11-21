from flask import Flask, request
from flask.json import jsonify

from device.Device import DeviceLocation, DeviceStatus
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


def start_detector_on_device(name, location, address, video_source):
    # todo implement this to connect to daemon on device and start new process there
    return None


@flask_app.route('/source', methods=['GET', 'POST'])
def manage_source():
    if request.method == 'GET':
        name = request.args.get('name')
        if name in device_container:
            device_info = dict()
            device_info['status'] = device_container.get_device_status(name).name
            device_info['location'] = device_container.get_device_location(name).name
            device_info['address'] = device_container.get_device_address(name)
            return jsonify(device_info)
        else:
            return 'unknown'

    if request.method == 'POST':
        print('POST Request received')
        name = request.form.get('name')
        new_status = request.form.get('status')
        new_status_enum = DeviceStatus[new_status]

        if name not in device_container:
            print('Starting new detector process')
            video_source = request.form.get('video_source')
            location = request.form.get('location')
            address = request.form.get('address')

            location_enum = DeviceLocation[location]
            device_container.add_device(name, location_enum, address, video_source)
            if DeviceStatus.ON == new_status_enum:
                device_container.start_device(name)

            return 'added device ' + name
        else:
            update_successful = device_container.handle_device_update(name, new_status_enum)
            return 'device ' + name + (' not' if update_successful else ' ') + 'updated'


if __name__ == '__main__':
    print('starting ipc server')
    ipc_server = AsyncServer(SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, message_handler)
    ipc_server.run()

    print('Starting flask_app')
    flask_app.run()
