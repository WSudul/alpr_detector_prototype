from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from app import device_container, flask_app
from app.forms import LoginForm, DeviceForm
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


def handle_device_update(name, new_status_enum, video_source, location_enum, address):
    if name not in device_container:
        print('Starting new detector process')

        device_container.add_device(name, location_enum, address, video_source)
        if DeviceStatus.ON == new_status_enum:
            device_container.start_device(name)

        return 'added device ' + name
    else:
        update_successful = device_container.handle_device_update(name, new_status_enum)
        return 'device ' + name + (' not' if update_successful else ' ') + 'updated'




@flask_app.route('/source', methods=['GET', 'POST'])
def manage_source():
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

    form = DeviceForm()
    if form.validate_on_submit():
        name = form.name.data
        new_status = form.status.data
        new_status_enum = DeviceStatus[new_status]
        video_source = form.video_source.data
        location = form.location.data
        location_enum = DeviceLocation[location]
        address = form.address.data
        success = handle_device_update(name, new_status_enum, video_source, location_enum, address)
        return redirect('index')
    else:

        return render_template('device.html', title='WebServer', form=form,
                               devices=device_container.get_devices_snapshot())
