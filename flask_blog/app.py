import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager


# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///blog.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from flask_blog.models.user import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models
    from flask_blog.models.user import User
    from flask_blog.models.post import Post, Category, Tag, post_tags
    from flask_blog.models.comment import Comment
    
    # Import routes
    from flask_blog.routes.auth import auth
    from flask_blog.routes.blog import blog
    
    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(blog)
    
    # Create all tables in the database
    db.create_all()
    
    # Create default categories if they don't exist
    categories = ['Technology', 'Programming', 'Web3', 'Business']
    for category_name in categories:
        if not Category.query.filter_by(name=category_name).first():
            category = Category(name=category_name)
            db.session.add(category)
    
    # Create default tags if they don't exist
    tags = ["Tech Trends",
            "AI & Machine Learning",
            "Cybersecurity",
            "Web Development",
            "Startup Life",
            "Remote Work",
            "Freelancing",
            "Python Programming",
            "Web3"
            ]
    for tag_name in tags:
        if not Tag.query.filter_by(name=tag_name).first():
            tag = Tag(name=tag_name)
            db.session.add(tag)
    
    db.session.commit()

        if not mongo.db.tags.find_one({'name': tag_name}):
            mongo.db.tags.insert_one({'name': tag_name})
