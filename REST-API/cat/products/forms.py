from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, BooleanField, DateTimeLocalField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from cat import ui_utils as utils
import pytz

class AddProductForm(FlaskForm):
    productname = StringField('Product Name*', validators=[DataRequired(), Length(min=1, max=200)])
    regex = StringField('Regular Expression', default='^[0-9]{4}-[0-9]{4}-[0-9]{6}$')
    strategy =  SelectField(u'Strategy', choices=['s1', 's2'])
    quota_over_days = IntegerField(u'Quota Over Days', default=1, validators=[NumberRange(1, 10)])
    max_days = IntegerField(u'Max Days', default=7, validators=[NumberRange(1, 30)])
    max_days_month = IntegerField(u'Max Days Month', default=300, validators=[NumberRange(1, 300)]) 
    sf_api = StringField('Salesforce API', validators=[Length(min=0, max=2000)])        
    sf_job_timezone = SelectField(u'Timezone*', choices=pytz.all_timezones, default="US/Pacific")
    sf_job_cron = StringField(u'Cron*', default="* 6-17 * * 0-4") 
    sf_product_series = StringField(u'Salesforce Product Series List(Comma Separated)*', validators=[Length(min=0, max=2000)]) 
    sf_platform = StringField(u'Salesforce Platform list(Comma Separated)', validators=[Length(min=0, max=2000)]) 
    sf_mist_product = StringField(u'Salesforce Mist Product Name', validators=[Length(min=0, max=2000)]) 
    sf_job_query_interval = IntegerField(u'Salesforce query interval in mins*', default=1, validators=[NumberRange(1, 600)])
    submit = SubmitField('Submit')
    sf_enabled = BooleanField(u'Enable Salesforce Integration', default=False)
    sf_init_email_name =  SelectField(u'Salesforce Initial Email Template', default='---')

    def validate_sf_job_timezone(form, field):
        if field.data == "" and form.sf_enabled.data is True:
            raise ValidationError("This field can not be empty if Salesforce is enabled")

    def validate_sf_job_cron(form, field):
        if field.data == "" and form.sf_enabled.data is True:
            raise ValidationError("This field can not be empty if Salesforce is enabled")

    def validate_sf_job_query_interval(form, field):
        if field.data == "" and form.sf_enabled.data is True:
            raise ValidationError("This field can not be empty if Salesforce is enabled")
    
    def validate_sf_product_series(form, field):
        if field.data == "" and form.sf_enabled.data is True:
            raise ValidationError("This field can not be empty if Salesforce is enabled")

class SheduleSFIntegrationForm(FlaskForm):
    productname = SelectField(u'Productname')
    datetime = DateTimeLocalField('When should the polling be activated or deactivated?', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    timezone = SelectField(u'Timezone', choices=pytz.all_timezones, default="US/Pacific")
    sf_enabled = BooleanField(u'Enable Salesforce Polling For New Cases', default=True)
    holiday_list = TextAreaField(u'A json formated list of holidays(Optional)', validators=[Length(max=5000)], render_kw={"rows": 5, "cols": 11})
    submit = SubmitField('Submit')