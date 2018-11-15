from collections import namedtuple
from threading import Thread

from detector.AlprDetector import AlprDetector, create_configuration, VIDEO_SOURCE, VIDEO_SOURCE_FILE
from ipc_communication.Client import Client
from ipc_communication.Server import Server
from ipc_communication.default_configuration import CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, SERVER_PREFIX

DetectorArgs = namedtuple('DetectorArgs', 'instance_name, alpr_configuration, video_source')
DetectorProcessArguments = namedtuple('DetectorProcessArguments', 'detector_args, client_address, client_port')


def run_detector_wrapper(detector):
    detector.run()


def start_detector_process(args):
    print('starting detector process')
    detector_args = args.detector_args
    client = Client(args.client_address, args.client_port)
    detector = AlprDetector(detector_args.instance_name, detector_args.alpr_configuration, detector_args.video_source,
                            client.send_message)

    print(detector.video_source_properties())
    detector_thread = Thread(target=run_detector_wrapper, args=[detector], daemon=True)
    detector_thread.start()

    detector_thread.join()
    print('Detector thread ended')
    client.disconnect(args.client_address, args.client_port)
    print('IPC Client disconnected')


def start_server(message_handler):
    print('starting server thread')
    ipc_server = Server(SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, message_handler)

    while True:
        ipc_server.receive_message()
        print('message received and handled')

    ipc_server.unbind(SERVER_PREFIX + ':' + str(DEFAULT_DETECTOR_SERVER_PORT))


def message_handler_callback(message):
    print('message_handler_callback')
    print(message)
    response = True
    return response


def main():
    server_thread = Thread(target=start_server, args=[message_handler_callback])
    server_thread.start()

    alpr_configuration = create_configuration()
    detector_arguments = DetectorArgs('detector1', alpr_configuration, VIDEO_SOURCE_FILE)
    new_process_args = DetectorProcessArguments(detector_arguments, CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)

    from concurrent.futures import ProcessPoolExecutor
    executor = ProcessPoolExecutor(max_workers=3)
    future_1 = executor.submit(start_detector_process, new_process_args)

    detector_arguments = DetectorArgs('detector2', alpr_configuration, VIDEO_SOURCE)
    new_process_args = DetectorProcessArguments(detector_arguments, CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)
    future_2 = executor.submit(start_detector_process, new_process_args)

    detector_arguments = DetectorArgs('detector3', alpr_configuration, 1)  # using 2nd webcam
    new_process_args = DetectorProcessArguments(detector_arguments, CLIENT_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)
    future_3 = executor.submit(start_detector_process, new_process_args)

    print(future_1.result(150))
    print(future_2.result(150))
    print(future_3.result(150))
    server_thread.join()


if __name__ == "__main__":
    main()
