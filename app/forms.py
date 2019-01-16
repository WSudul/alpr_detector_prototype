from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, InputRequired

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
    status = StringField(_l('Status'), validators=[DataRequired(), device_status_check])
    video_source = StringField(_l('Video source'), validators=[DataRequired()])
    address = StringField(_l('Address'), validators=[DataRequired()])
    listener_port = IntegerField(_l('Listener Port'), validators=[DataRequired()])
    location = StringField(_l('Location'), validators=[DataRequired(), device_location_check])
    capture = BooleanField(_l('Capture images'))

    submit = SubmitField(_l('Submit device creation'))


class UpdateDeviceForm(FlaskForm):
    name = StringField(_l('Device'), validators=[InputRequired()])
    status = StringField(_l('Status'), validators=[device_status_check])
    video_source = StringField(_l('Video source'))
    address = StringField(_l('Address'))
    listener_port = IntegerField(_l('Listener Port'))
    capture = BooleanField(_l('Capture images'))

    submit = SubmitField(_l('Submit device update'))

