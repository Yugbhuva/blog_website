from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length

class PostForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=3, max=120, message='Title must be between 3 and 120 characters')
    ])
    
    content = TextAreaField('Content', validators=[
        DataRequired(),
        Length(min=10, message='Content must be at least 10 characters')
    ])
    
    category_id = SelectField('Category', coerce=int, validators=[
        DataRequired(message='Please select a category')
    ])
    
    tags = SelectMultipleField('Tags', coerce=int)
    
    published = BooleanField('Publish Immediately', default=True)
    
    submit = SubmitField('Save Post')
