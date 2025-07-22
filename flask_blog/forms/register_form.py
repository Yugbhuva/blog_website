from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_blog.app import mongo

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address'),
        Length(min=5, max=120)
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=50, message='Password must be at least 6 characters')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    
    bio = TextAreaField('About Me', validators=[
        Length(max=500, message='Bio must be less than 500 characters')
    ])
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = mongo.db.users.find_one({'username': username.data})
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = mongo.db.users.find_one({'email': email.data})
        if user:
            raise ValidationError('Email is already registered. Please use a different one.')
