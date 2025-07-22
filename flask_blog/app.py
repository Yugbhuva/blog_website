import os
import logging

from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# configure the database
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/blog_db")
mongo = PyMongo(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # You will need to implement this for MongoDB
    from flask_blog.models.user import get_user_by_id
    return get_user_by_id(user_id)

with app.app_context():
    # Import routes
    from flask_blog.routes.auth import auth
    from flask_blog.routes.blog import blog
    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(blog)
