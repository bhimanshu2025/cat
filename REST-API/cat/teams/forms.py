from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Email, optional

class AddTeamForm(FlaskForm):
    teamname = StringField('Teamname*', validators=[DataRequired(), Length(min=1, max=200)])
    email =  StringField('Email', validators=[optional(), Email()])
    mswebhook =  StringField('Microsoft Teams Webhook')
    submit = SubmitField('Submit')