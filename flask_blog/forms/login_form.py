from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(min=5, max=120)
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=50)
    ])
    
    remember_me = BooleanField('Remember Me')
    
    submit = SubmitField('Sign In')
