import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # MongoDB configuration
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/blog_db")
    
    # Application configuration
    POSTS_PER_PAGE = 5
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

# Select configuration based on environment
config = {
    'development': Config,
    'production': Config,
    'default': Config
}
