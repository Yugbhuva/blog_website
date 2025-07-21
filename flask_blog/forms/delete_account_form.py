from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class DeleteAccountForm(FlaskForm):
    password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        Length(min=6, max=50, message='Password must be at least 6 characters')
    ])
    submit = SubmitField('Delete My Account')