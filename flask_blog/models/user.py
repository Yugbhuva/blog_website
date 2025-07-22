from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_blog.app import mongo
from bson import ObjectId

class MongoUser(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.username = user_doc['username']
        self.email = user_doc['email']
        self.password_hash = user_doc['password_hash']
        self.bio = user_doc.get('bio')
        self.date_joined = user_doc.get('date_joined')
        self.last_login = user_doc.get('last_login')
        self.is_admin = user_doc.get('is_admin', False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get(user_id):
        user_doc = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_doc:
            return MongoUser(user_doc)
        return None

def get_user_by_id(user_id):
    return MongoUser.get(user_id)

def create_user(username, email, password, bio=None):
    from datetime import datetime
    user = {
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'bio': bio,
        'is_admin': False,
        'date_joined': datetime.utcnow()
    }
    result = mongo.db.users.insert_one(user)
    user['_id'] = result.inserted_id
    return MongoUser(user)
