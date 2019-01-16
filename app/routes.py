from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from app import device_container, flask_app
from app.forms import LoginForm, DeviceForm, UpdateDeviceForm
from app.models import User
from device.Device import DeviceStatus, DeviceLocation


@flask_app.route('/')
@flask_app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')


@flask_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    else:
        return render_template('login.html', title='Sign In', form=form)


@flask_app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@flask_app.route('/status', methods=['GET'])
def status():
    return 'Current avaiable sources: \n' + str(device_container.get_list_of_devices())


def handle_device_update(name, new_status_enum, video_source, location_enum, address, listener_port):
    if name not in device_container:
        print('Starting new detector process')

        if video_source.isdigit():
            print('Interpreting video source as device id')
            video_source = int(video_source)

        device_container.add_device(name, location_enum, address, listener_port, video_source)
        if DeviceStatus.ON == new_status_enum:
            device_container.start_device(name)

        return 'added device ' + name
    else:
        update_successful = device_container.handle_device_update(name, new_status_enum, address, listener_port,
                                                                  video_source)
        return 'device ' + name + (' not ' if update_successful else ' ') + 'updated'


@flask_app.route('/source', methods=['GET'])
def get_info():
    name = request.args.get('name')
    if name is not None:
        if name in device_container:
            device_info = dict()
            device_info['status'] = device_container.get_device_status(name).name
            device_info['location'] = device_container.get_device_location(name).name
            device_info['address'] = device_container.get_device_address(name)
            return jsonify(device_info)
        else:
            return 'unknown'


def obtain_device_names(container):
    device_names = [(i, i) for i in
                    container] if not container else [('', '')]
    print('Known devices: ', device_names)
    return device_names


@flask_app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    form_create = DeviceForm()
    # device_names = obtain_device_names(device_container.get_list_of_devices())
    form_update = UpdateDeviceForm()  # UpdateDeviceForm(choices=device_names)

    if form_create.validate_on_submit():
        print('Adding new device')
        name = form_create.name.data
        new_status = form_create.status.data
        new_status_enum = DeviceStatus[new_status]
        video_source = form_create.video_source.data
        location = form_create.location.data
        location_enum = DeviceLocation[location]
        address = form_create.address.data
        listener_port = form_create.listener_port.data
        response = handle_device_update(name, new_status_enum, video_source, location_enum, address, listener_port)
        flash(response)

    return render_template('device.html', title='WebServer', create_form=form_create, update_form=form_update,
                           devices=device_container.get_devices_snapshot())


@flask_app.route('/update_device', methods=['GET', 'POST'])
def update_device():
    form_create = DeviceForm()
    # device_names = obtain_device_names(device_container.get_list_of_devices())
    form_update = UpdateDeviceForm()  # UpdateDeviceForm(choices=device_names)

    if form_update.validate_on_submit():
        print('Updating existing device')
        name = form_update.name.data
        new_status = form_update.status.data
        new_status_enum = DeviceStatus[new_status]
        video_source = form_create.video_source.data
        address = form_update.address.data
        listener_port = form_update.listener_port.data
        response = handle_device_update(name, new_status_enum, video_source, None, address, listener_port)
        flash(response)

    return render_template('device.html', title='WebServer', create_form=form_create, update_form=form_update,
                           devices=device_container.get_devices_snapshot())
