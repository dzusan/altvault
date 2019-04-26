from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from wtforms.widgets.html5 import NumberInput

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class SearchForm(FlaskForm):
    searchField = StringField('Search', validators=[DataRequired()])
    searchButton = SubmitField('Search')

class LocalResultForm(FlaskForm):
    table = HiddenField('Table')
    part = HiddenField('Part')
    cell = StringField('Cell', validators=[DataRequired()])
    quantity = IntegerField('Quantity', widget=NumberInput(min=0, max=9999),
                             validators=[DataRequired(), NumberRange(min=0, max=9999)])
    update = SubmitField('Update')
