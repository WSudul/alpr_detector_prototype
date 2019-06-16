from app import db, flask_app
from app.models import User



@flask_app.shell_context_processor
def make_shell_context():
    print('shell_context_processor')
    return {'db': db, 'User': User}


if __name__ == '__main__':
    print('starting ipc server')
    # ipc_server = AsyncServer(SERVER_PREFIX, DEFAULT_DETECTOR_SERVER_PORT, message_handler)
    # ipc_server.run()



    print('Starting flask_app')
    flask_app.run(

    )
else:
    print('starting via flask run command')
    with flask_app.app_context():
        db.create_all()
        # test_user = User()
        # test_user.username = 'test'
        # test_user.email = 'test@test.com'
        # test_user.set_password('test')
        # db.session.add(test_user)
        # db.session.commit()
