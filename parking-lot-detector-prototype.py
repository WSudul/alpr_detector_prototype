from multiprocessing import Process

from flask import Flask, request

from detector.AlprDetector import AlprConfiguration, FRAME_SKIP
from detector.DetectorProcessWrapper import DetectorArgs, DetectorProcessArguments, CommunicationConfiguration, \
    AddressAndPort, start_detector_process
from ipc_communication.Server import AsyncServer
from ipc_communication.default_configuration import SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, CLIENT_PREFIX

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


sources = {}


@flask_app.route('/')
def hello_world():
    return 'Hello World!'


@flask_app.route('/status', methods=['GET'])
def status():
    return 'Current running sources: \n' + str(sources)


def start_detector(video_source, name):
    alpr_configuration = AlprConfiguration('eu', 'resources/openalpr.conf', 'resources/runtime_data', FRAME_SKIP)
    detector_arguments = DetectorArgs('detector1', alpr_configuration, video_source)
    new_process_args = DetectorProcessArguments(name, detector_arguments,
                                                CommunicationConfiguration(
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT),
                                                    AddressAndPort(CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)))

    print('Starting new process with config:\n', new_process_args)
    process = Process(target=start_detector_process, args=(new_process_args,))
    process.start()


@flask_app.route('/source', methods=['GET', 'POST'])
def manage_source():
    if request.method == 'GET':
        name = request.args.get('name')
        if name in sources:
            source_status = sources[name]
        else:
            source_status = 'unknown'
        return 'Source status: ' + source_status

    if request.method == 'POST':
        print('POST Request received')
        name = request.form.get('name')
        new_status = request.form.get('status')

        if name not in sources:
            print('Starting new detector process')
            video_source = request.form.get('video_source')
            start_detector(video_source, name)
            sources[name] = 'STARTED'
        else:
            # todo handle update
            sources[name] = new_status

        return 'updated'


if __name__ == '__main__':
    print('starting ipc server')
    ipc_server = AsyncServer(SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, message_handler)
    ipc_server.run()

    print('Starting flask_app')
    flask_app.run()
