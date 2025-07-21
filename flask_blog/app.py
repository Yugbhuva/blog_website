import os
import logging
import markdown

from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# configure the MongoDB database
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/blog_db")

# initialize the app with the extension
mongo = PyMongo(app)

# Custom Jinja2 filter for Markdown
@app.template_filter('markdown')
def markdown_filter(s):
    return markdown.markdown(s)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from flask_blog.models.user import User
    return User.get_by_id(user_id)

with app.app_context():
    # Import models
    from flask_blog.models.user import User
    from flask_blog.models.post import Post, Category, Tag
    from flask_blog.models.comment import Comment
    
    # Import routes
    from flask_blog.routes.auth import auth
    from flask_blog.routes.blog import blog
    
    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(blog)
    
    # Create default categories if they don't exist
    categories = ['Technology', 'Programming', 'Web3', 'Business']
    for category_name in categories:
        if not mongo.db.categories.find_one({'name': category_name}):
            mongo.db.categories.insert_one({'name': category_name, 'description': ''})

    # Create default tags if they don't exist
    tags = ["Tech Trends", "AI & Machine Learning", "Cybersecurity", "Web Development", "Startup Life", "Remote Work", "Freelancing", "Python Programming", "Web3"]
    for tag_name in tags:
        if not mongo.db.tags.find_one({'name': tag_name}):
            mongo.db.tags.insert_one({'name': tag_name})
