import json

import requests
from flask import Flask
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from requests import RequestException

from config import Config
from device.DeviceContainer import DeviceContainer
from gpio.leds import LedController
from ipc_communication.Server import AsyncServer
from ipc_communication.default_configuration import SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT

login_manager = LoginManager()
login_manager.login_view = 'login'

db = SQLAlchemy()
migrate = Migrate()

bootstrap = Bootstrap()
babel = Babel()

device_container = DeviceContainer()

led_controller = LedController()


def prepare_request(message):
    request_data = dict()
    request_data['requester'] = 'Parking-Krk-1'
    plates = [item[0] for item in message['candidates']]
    request_data['plates'] = plates
    return json.dumps(request_data)


def message_handler(message):
    led_controller.progress()
    post_request_data = prepare_request(message)

    base_addr = 'https://test-lot.herokuapp.com'
    endpoint = base_addr + '/gate/'  # 'http://localhost:8080/parking/gate/'
    if message['detector_role'] == 'ENTRY':
        endpoint += 'entrance'
    else:
        endpoint += 'departure'
    print("endpoint: ", endpoint)

    try:
        print('sending request to: ', endpoint)
        headers = {'content-type': 'application/json'}
        response = requests.post(endpoint, data=post_request_data, headers=headers)
        result = response.json().get('validation')
    except (RequestException, ConnectionError) as e:
        print(e)
        return False
    print('response = ', response)
    from time import sleep
    sleep(0.1)

    if response.status_code is 200 and result is not None and result is True:
        led_controller.success()
        return True

    else:
        led_controller.failure()
        return False

    # print('response: ', response.status_code)


ipc_server = AsyncServer(message_handler)


def create_app(config_class=Config):
    print('using create_app to create flask app object')
    import zmq.error
    try:
        ipc_server.bind(SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT)
        # ipc_server.bind(SERVER_PREFIX_LOCAL, DEFAULT_DETECTOR_SERVER_PORT)
        ipc_server.run()
    except zmq.ZMQError as e:
        print('Exception during bind process: ', e, ' - ', e.errno)
        exit(-1)

    app = Flask(__name__)
    app.config.from_object(config_class)

    login_manager.init_app(app)
    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)

    return app


flask_app = create_app()

from app import routes, models
