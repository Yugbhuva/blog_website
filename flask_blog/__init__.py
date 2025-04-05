from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create SQLAlchemy instance
db = SQLAlchemy()

def create_app(config_name='default'):
    app = Flask(__name__)

    # Load configuration
    from flask_blog.config import config
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)

    # Register your blueprints here if any
    # from flask_blog.routes.main import main as main_blueprint
    # app.register_blueprint(main_blueprint)

    return app

# For WSGI use
app = create_app()
