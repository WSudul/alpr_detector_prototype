import datetime
import cv2
from openalpr import Alpr
import sys

VIDEO_SOURCE = '../resources/videos/eu-clip.mp4'
WINDOW_NAME = 'openalpr'
FRAME_SKIP = 5


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

    cv2.destroyAllWindows()
    cap.release()
    alpr.unload()


if __name__ == "__main__":
    main()
