from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, IntegerField, RadioField, SelectField
from wtforms.validators import DataRequired, NumberRange
from wtforms.widgets.html5 import NumberInput

from app import selectors
import DBstructure

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

class GenForm(FlaskForm):
    parts = RadioField('UID')
    authors = RadioField('Author')
    gen = SubmitField('Generate')

class AddForm(FlaskForm):
    add = SubmitField('Add')

def gen_add_form(data=None):
    fieldnames = {name.replace(' ', '_'):name for name in DBstructure.colNames}
    
    for key, name in fieldnames.items():
        if key == 'Author':
            if data:
                setattr(AddForm, 'Author', SelectField('Author', choices=selectors.author(), default=data['Author']))
            else:
                setattr(AddForm, 'Author', SelectField('Author', choices=selectors.author()))
        else:
            if data:
                setattr(AddForm, key, StringField(name, default=data[key]))
            else:
                setattr(AddForm, key, StringField(name))
    
    add_form = AddForm()
    return fieldnames, add_form


