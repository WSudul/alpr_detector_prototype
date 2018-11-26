from flask import Flask
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config
from device.DeviceContainer import DeviceContainer
from ipc_communication.Server import AsyncServer
from ipc_communication.default_configuration import SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT

login_manager = LoginManager()
login_manager.login_view = 'login'

db = SQLAlchemy()
migrate = Migrate()

bootstrap = Bootstrap()

babel = Babel()

device_container = DeviceContainer()


def message_handler(message):
    print('handling message: ', message)


ipc_server = AsyncServer(SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, message_handler)


def create_app(config_class=Config):
    print('using create_app to create flask app object')
    # ipc_server.run() # TODO uncomment this

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
