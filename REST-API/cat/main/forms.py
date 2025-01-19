from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, RadioField
from wtforms.validators import DataRequired, Length
from flask import current_app
from cat import ui_utils as utils

class CaseIdForm(FlaskForm):
    caseid = SelectField(u'Case ID')  
    caseid_text = StringField('OR Type the case ID')
    # priority = RadioField(u'Priority*', choices=current_app.config['PRIORITY_LIST'], default='P2')
    mode = SelectField(u'Mode', choices=['auto', 'manual', 'auto-reassign'])
    user = SelectField(u'Username', default='---')
    sf_email_name = SelectField(u'Salesforce Email', default='---')
    delayed_assignment = SelectField(u'Delayed Assignment', choices=utils.get_time_list(diff=30) + ['---'], default='---')
    comments = StringField('Comments')
    # sf_account_name = StringField('Customer/Account Name',validators=[Length(min=0, max=2000)])
    '''
    Fetch product list when the form is loaded as current_user is called to get list of product currentuser supports
    '''
    product = SelectField(u'Product', default='---')
    submit = SubmitField('Submit')
    check_in_shift = BooleanField(u'Check if user is in shift or not', default=True)

class CaseUnassignForm(FlaskForm):
    '''
    Fetch cases list when the form is loaded as current_user is called in the get_cases_list function and that user isnt loaded when application is started
    '''
    caseid = SelectField(u'Case ID')  
    caseid_text = StringField('OR Type the case ID')
    comments = StringField('Comments*', validators=[DataRequired()])
    submit = SubmitField('Submit')
