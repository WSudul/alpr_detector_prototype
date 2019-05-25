from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo

from device.Device import DeviceStatus, DeviceLocation


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))


def device_status_check(form, field):
    if DeviceStatus.UNKNOWN.name.upper() == field.data.upper():
        raise ValidationError('Illegal state provided. Acceptable states: ' +
                              str(list(map(lambda c: c.name, DeviceLocation))))

    for status in DeviceStatus:
        if status.name.upper() == field.data.upper():
            return

    raise ValidationError('Illegal state provided. Acceptable states: ' +
                          str(list(map(lambda c: c.name, DeviceLocation))))


def device_location_check(form, field):
    for status in DeviceLocation:
        if status.name.upper() == field.data.upper():
            return

    raise ValidationError('Illegal state provided. Acceptable states: ' +
                          str(list(map(lambda c: c.name, DeviceLocation))))


class DeviceForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired()])
    status = SelectField(_l('Initial Status', choices=[('ON', 'ON'), ('OFF', 'OFF')]))
    video_source = StringField(_l('Video source'), validators=[DataRequired()])
    address = StringField(_l('Address'), validators=[DataRequired()])
    listener_port = IntegerField(_l('Listener Port'), validators=[DataRequired()])
    role = SelectField(_l('Role', choices=[('ENTRY', 'ENTRY'), ('EXIT', 'EXIT')]))
    capture = BooleanField(_l('Capture images'))

    submit = SubmitField(_l('Submit device creation'))


class UpdateDeviceForm(FlaskForm):
    name = SelectField(_l('Device'))
    status = SelectField(_l('New Status', choices=[('ON', 'ON'), ('OFF', 'OFF')]))
    video_source = StringField(_l('Video source'))
    address = StringField(_l('Address'))
    listener_port = IntegerField(_l('Listener Port'))
    role = SelectField(_l('Role', choices=[('ENTRY', 'ENTRY'), ('EXIT', 'EXIT')]))
    capture = BooleanField(_l('Capture images'))

    submit = SubmitField(_l('Submit device update'))
