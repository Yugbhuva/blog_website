from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[
        DataRequired(),
        Length(min=2, max=1000, message='Comment must be between 2 and 1000 characters')
    ])
    
    parent_id = HiddenField('Parent Comment ID')
    
    submit = SubmitField('Post Comment')
