import gpiozero
from gpiozero import LED

from gpiozero.pins.mock import MockFactory

gpiozero.Device.pin_factory = MockFactory()


class LedController:
    def __init__(self):
        self.green_led = LED(27)
        self.red_led = LED(28)
        self.yellow_led = LED(29)

    def success(self):
        self.green_led.blink(2)

    def failure(self):
        self.red_led.blink(2)

    def progress(self):
        self.yellow_led.blink(0.5, 0.5, 5)
