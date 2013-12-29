from flask.ext.wtf import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required, NumberRange

class SubmitForm(Form):
    weight = TextField('weight', validators=[Required()])
    parachute = TextField('parachute', validators=[Required()])
    balloon = TextField('balloon', validators=[Required()])
    helium = TextField('helium', validators=[Required()])
    callsign = TextField('callsign', validators=[Required()])
