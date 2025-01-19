from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField, BooleanField, DateTimeLocalField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange
from cat import ui_utils as utils
import pytz

class AddUserForm(FlaskForm):
    username = StringField('Username*', validators=[DataRequired(), Length(min=1, max=50)])
    first_name = StringField('First Name', validators=[Length(min=0, max=50)])
    last_name = StringField('Last Name', validators=[Length(min=0, max=50)])
    email = StringField('Email*', validators=[Email()])
    teamname = SelectField('Teamname')
    password = PasswordField('Password*', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password*', 
                                     validators=[DataRequired(), EqualTo('password')])
    timezone = SelectField(u'Timezone', choices=pytz.all_timezones, default="US/Pacific")
    shift_start = SelectField(u'Shift Start Time', choices=utils.get_time_list(), default="09:00:00")
    shift_end = SelectField(u'Shift End Time', choices=utils.get_time_list(), default="18:00:00")
    admin = BooleanField(u'Admin')
    active = BooleanField(u'Active', default=True)
    team_email_notifications = BooleanField(u'Receive Team Activity Email Notifications?', default=False)
    monitor_case_updates = BooleanField(u'Monitor For External Case Updates During My Absence?', default=False)
    submit = SubmitField('Submit')

class AccountForm(FlaskForm):
    email = StringField('Email', validators=[Email()])
    timezone = SelectField(u'Timezone', choices=pytz.all_timezones, default="US/Pacific")
    active = BooleanField(u'Active', default=True)
    team_email_notifications = BooleanField(u'Recieve Team Activity Email Notifications?', default=False)
    monitor_case_updates = BooleanField(u'Monitor For External Case Updates During My Absence?', default=False)
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    muleuser = BooleanField('Use Mule Account?')
    submit = SubmitField('Login')

class ReactivateUserForm(FlaskForm):
    username = SelectField(u'Username')
    datetime = DateTimeLocalField('When should the user be activated or deactivated?', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    timezone = SelectField(u'Timezone', choices=pytz.all_timezones, default="US/Pacific")
    active = BooleanField(u'Active', default=True)
    submit = SubmitField('Submit')

class ScheduleShiftChangerForm(FlaskForm):
    username = SelectField(u'Username')
    datetime = DateTimeLocalField('When should the user shift be changed?', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    timezone = SelectField(u'Timezone', choices=pytz.all_timezones, default="US/Pacific")
    shift_start = SelectField(u'Shift Start Time', choices=utils.get_time_list(), default="09:00:00")
    shift_end = SelectField(u'Shift End Time', choices=utils.get_time_list(), default="18:00:00")
    submit = SubmitField('Submit')

class ScheduleHandoffsForm(FlaskForm):
    username = SelectField(u'Username')
    datetime = DateTimeLocalField("When should the users cases be CAT'ed?", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    timezone = SelectField(u'Timezone', choices=pytz.all_timezones, default="US/Pacific")
    check_in_shift = BooleanField(u"Check if users are in shift or not when CAT'ing", default=False)
    submit = SubmitField('Submit')

class AddUserProductForm(FlaskForm):
    productname = SelectField(u'Product Name')
    username = SelectField(u'Username')
    active = BooleanField(u'Active', default=True)
    quota = IntegerField(u'Quota', default=1, validators=[NumberRange(1, 10)])                
    submit = SubmitField('Submit')

class AddSalesforceEmailForm(FlaskForm):
    email_name = StringField(u'Name')
    email_body = TextAreaField(u'Email Body(Refer Jinja2 Variables under My Stuff to use variables)', validators=[Length(max=5000)], render_kw={"rows": 20, "cols": 11})
    email_subject = StringField(u'Email Subject')              
    submit = SubmitField('Submit')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password*', validators=[DataRequired()])
    new_password = PasswordField('New Password*', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirm New Password*', 
                                     validators=[DataRequired(), EqualTo('new_password')]) 
    submit = SubmitField('Submit')

class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[Email()])
    submit = SubmitField('Submit')