import datetime
from collections import namedtuple

import cv2
from openalpr import Alpr

VIDEO_SOURCE = 0  # default webcam address
VIDEO_SOURCE_FILE = '../resources/videos/hispeed.mp4'
WINDOW_NAME = 'openalpr'
FRAME_SKIP = 12

AlprConfiguration = namedtuple('AlprConfiguration', 'region, config_file, runtime_data_file, frame_skip')
AlprDetectorArgs = namedtuple('AlprDetectorArgs', 'instance_name, alpr_configuration, video_source, capture_images, '
                                                  'role')


def video_source_properties(cap):
    data = dict()
    data['fps'] = cap.get(cv2.CAP_PROP_FPS)
    data['width'] = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    data['height'] = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    data['codec'] = cap.get(cv2.CAP_PROP_FOURCC)
    return 'Video source properties ' + str(data)


class AlprDetector:

    def __init__(self, name, config, video_source, event_callback=None, save_images=False):
        self.__name = name
        self.__alpr_instance = Alpr(config.region, config.config_file, config.runtime_data_file)
        if not self.__alpr_instance.is_loaded():
            print('Alpr instance could not be created')
        self.__frame_skip = config.frame_skip
        self.event_callback = event_callback
        self.__video_source = video_source
        self.__cap = cv2.VideoCapture(video_source)
        self.__running = False
        self.__save_image = save_images
        import os
        self.__directory = os.getcwd()

    def is_working(self):
        return self.__cap.isOpened() and self.__running

    def video_source_properties(self):
        data = dict()
        data['source'] = self.__video_source
        data['fps'] = self.__cap.get(cv2.CAP_PROP_FPS)
        data['width'] = self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        data['height'] = self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        data['codec'] = self.__cap.get(cv2.CAP_PROP_FOURCC)
        return

    @staticmethod
    def __extract_results(alpr_result):
        if alpr_result is None:
            return None
        if not alpr_result['results']:
            return None
        else:
            result = []
            for plate in alpr_result['results']:
                for candidate in plate['candidates']:
                    result.append([candidate['plate'], candidate['confidence']])
            return result

    @staticmethod
    def __extract_best_candidate(alpr_result):
        return alpr_result['results'][0]['plate'] if alpr_result['results'] else None

    def __handle_results(self, extracted_results):
        if self.event_callback is not None:
            callback_data = dict()
            # object is list of dict containing 'plate' and 'confidence'
            callback_data['candidates'] = extracted_results
            callback_data['detector'] = self.__name
            print('calling callback , ', extracted_results)
            self.event_callback(callback_data)

    def run(self):
        if self.__running:
            print(self.__name, ' Detector is already running')
            return False
        else:
            self.__running = True

        if not self.is_working():
            print(self.__name, ' Video capture not working.')
            self.__running = False
            return False

        frame_number = 0
        last_recognized_plate = None
        error_state = False
        try:
            print(self.__name, ' starting detector loop for: ', self.__video_source)
            while self.__running:
                a = datetime.datetime.now()
                last_read_status, frame = self.__cap.read()
                if not last_read_status:
                    print('Video capture.read() failed. Stopping the work')
                    self.__running = False
                    error_state = True
                    break
                frame_number += 1
                if frame_number % self.__frame_skip == 0:
                    frame_number = 0
                    continue
                if cv2.waitKey(1) == 27:
                    break
                # cv2.imshow(self.__name, frame)

                # todo: use recognize_ndarray when updated to at least 2.3.1
                # alpr.recognize_ndarray(frame)
                ret, enc = cv2.imencode("*.bmp", frame)
                results = self.__alpr_instance.recognize_array(bytes(bytearray(enc)))
                best_candidate = self.__extract_best_candidate(results)
                if best_candidate is not None and best_candidate != last_recognized_plate:
                    last_recognized_plate = best_candidate
                    print(best_candidate)
                    # send first recognized plate and all candidates
                    extracted_results = self.__extract_results(results)
                    if extracted_results:
                        self.__handle_results(extracted_results)

                    if self.__save_image:
                        print(self.__directory)
                        import os.path
                        cv2.imwrite(os.path.join(self.__directory,
                                                 self.__name,
                                                 ''.join((best_candidate, '_',
                                                          self.__name, '_',
                                                          datetime.datetime.now().strftime(
                                                              "%Y_%m_%d_%H_%M_%S"),
                                                          '.jpeg'))), frame)

        except cv2.error as e:
            print("OpenCV Exception caught: ", e)
            error_state = True
        except Exception as e:
            print("Exception caught: ", e)
            error_state = True
        finally:
            self.__alpr_instance.unload()
            self.__running = False
            print(self.__name, " is stopping")
            return not error_state

    def stop(self):
        self.__running = False


def create_configuration():
    alpr_configuration = AlprConfiguration('eu', '../resources/openalpr.conf', '../resources/runtime_data', FRAME_SKIP)
    return alpr_configuration


def run_detector(alpr_configuration, instance_name, video_source):
    detector = AlprDetector(instance_name, alpr_configuration, video_source)
    print('is working : ', detector.is_working())

    print(detector.video_source_properties())

    return detector.run()


def main():
    alpr_configuration = create_configuration()

    run_detector(alpr_configuration, "detector_2", VIDEO_SOURCE_FILE)


if __name__ == "__main__":
    main()
