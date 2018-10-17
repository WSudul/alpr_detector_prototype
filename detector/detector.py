import datetime
import cv2
from openalpr import Alpr
import sys

VIDEO_SOURCE = 0  # default webcam address
WINDOW_NAME = 'openalpr'
FRAME_SKIP = 12


def video_source_properties(cap):
    data = dict()
    data['fps'] = cap.get(cv2.CAP_PROP_FPS)
    data['width'] = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    data['height'] = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    data['codec'] = cap.get(cv2.CAP_PROP_FOURCC)
    print('Video source properties ', str(data))


class Detector:

    def __init__(self, alpr_instance, video_source, frame_skip=FRAME_SKIP):
        self.alpr_instance = alpr_instance
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
        frame_number = 0
        while self._running:
            last_read_status, frame = self._cap.read()

            if not last_read_status:
                print('VidepCapture.read() failed. Exiting...')
                self._running = False
                break

            frame_number += 1
            if frame_number % self.frame_skip != 0:
                continue

            ret, enc = cv2.imencode("*.bmp", frame)
            results = self.alpr.recognize_array(bytes(bytearray(enc)))

            # todo: use recognize_ndarray when updated to at least 2.3.1
            # alpr.recognize_ndarray(frame)
            for i, plate in enumerate(results['results']):
                best_candidate = plate['candidates'][0]
                print('Plate #{}: {:7s} ({:.2f}%)'.format(i, best_candidate['plate'].upper(),
                                                          best_candidate['confidence']))

    def stop(self):
        self._running = False
        
def main():
    alpr = Alpr('eu', '../resources/openalpr.conf', '../resources/runtime_data')
    if not alpr.is_loaded():
        print('Error loading OpenALPR')
        sys.exit(1)
    alpr.set_top_n(3)
    # alpr.set_default_region('new')
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        alpr.unload()
        sys.exit('Failed to open video file!')

    video_source_properties(cap)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.setWindowTitle(WINDOW_NAME, 'OpenALPR video test')

    _frame_number = 0
    a = datetime.datetime.now()
    while True:
        ret_val, frame = cap.read()

        if not ret_val:
            print('VidepCapture.read() failed. Exiting...')
            b = datetime.datetime.now()
            c = b - a
            print(c.total_seconds(), c.seconds, c.microseconds)
            break

        _frame_number += 1
        if _frame_number % FRAME_SKIP != 0:
            continue
        cv2.imshow(WINDOW_NAME, frame)

        ret, enc = cv2.imencode("*.bmp", frame)
        results = alpr.recognize_array(bytes(bytearray(enc)))

        # todo: use recognize_ndarray when updated to at least 2.3.1
        # alpr.recognize_ndarray(frame)
        for i, plate in enumerate(results['results']):
            best_candidate = plate['candidates'][0]
            print('Plate #{}: {:7s} ({:.2f}%)'.format(i, best_candidate['plate'].upper(), best_candidate['confidence']))

        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()
    cap.release()
    alpr.unload()


if __name__ == "__main__":
    main()
