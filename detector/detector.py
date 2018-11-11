import datetime
from collections import namedtuple

import cv2
from openalpr import Alpr
import sys

VIDEO_SOURCE = 0  # default webcam address
VIDEO_SOURCE_FILE = '../resources/videos/hispeed.mp4'
WINDOW_NAME = 'openalpr'
FRAME_SKIP = 12

AlprConfiguration = namedtuple('AlprConfiguration', 'region, config_file, runtime_data_file, frame_skip')


def video_source_properties(cap):
    data = dict()
    data['fps'] = cap.get(cv2.CAP_PROP_FPS)
    data['width'] = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    data['height'] = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    data['codec'] = cap.get(cv2.CAP_PROP_FOURCC)
    print('Video source properties ', str(data))


class Detector:

    def __init__(self, name, config, video_source, frame_skip=FRAME_SKIP):
        self._name = name
        self.alpr_instance = Alpr(config.region, config.config_file, config.runtime_data_file)
        if not self.alpr_instance.is_loaded():
            print('Alpr instance could not be created')
        self.frame_skip = frame_skip
        self._video_source = video_source
        self._cap = cv2.VideoCapture(video_source)
        self._running = False

    def is_working(self):
        return self._cap.isOpened() and self._running

    def video_source_properties(self):
        data = dict()
        data['source'] = self._video_source
        data['fps'] = self._cap.get(cv2.CAP_PROP_FPS)
        data['width'] = self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        data['height'] = self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        data['codec'] = self._cap.get(cv2.CAP_PROP_FOURCC)
        return data

    def run(self):
        if self._running:
            print('Detector is already running')
            return False
        else:
            self._running = True

        if not self.is_working():
            print('Video capture not working.');
            return False

        frame_number = 0
        error_state = False
        try:
            print(self._name, ' starting detector loop')
            while self._running:
                last_read_status, frame = self._cap.read()

                if not last_read_status:
                    print('Video capture.read() failed. Stopping the work')
                    self._running = False
                    error_state = True
                    break

                frame_number += 1
                if frame_number % self.frame_skip != 0:
                    frame_number = 0
                    continue

                ret, enc = cv2.imencode("*.bmp", frame)
                results = self.alpr.recognize_array(bytes(bytearray(enc)))

                # todo: use recognize_ndarray when updated to at least 2.3.1
                # alpr.recognize_ndarray(frame)
                for i, plate in enumerate(results['results']):
                    best_candidate = plate['candidates'][0]
                    print(self._name, ' Plate #{}: {:7s} ({:.2f}%)'.format(i, best_candidate['plate'].upper(),
                                                                           best_candidate['confidence']))
        except cv2.error as e:
            print("OpenCV Exception caught: ", e)
            error_state = True
        except Exception as e:
            print("Exception caught: ", e)
            error_state = True
        finally:
            self.alpr_instance.unload()
            print(self._name, " is stopping")
            return not error_state

    def stop(self):
        self._running = False


def create_configuration():
    alpr_configuration = AlprConfiguration('eu', '../resources/openalpr.conf', '../resources/runtime_data', FRAME_SKIP)
    return alpr_configuration


def run_detector(alpr_configuration, instance_name, video_source):
    detector = Detector(instance_name, alpr_configuration, video_source)
    print('is working : ', detector.is_working())

    print(detector.video_source_properties())

    return detector.run()


def main():
    alpr_configuration = create_configuration()

    from concurrent.futures import ProcessPoolExecutor
    executor = ProcessPoolExecutor(max_workers=2)
    print('submiting detector')
    future_1 = executor.submit(run_detector, alpr_configuration, "detector_1", VIDEO_SOURCE)
    future_2 = executor.submit(run_detector, alpr_configuration, "detector_2", VIDEO_SOURCE_FILE)
    print('got future')
    import time
    time.sleep(1)
    print(future_1.result(150))
    print(future_2.result(150))


if __name__ == "__main__":
    main()
