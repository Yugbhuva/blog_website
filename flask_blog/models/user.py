from datetime import datetime
from flask_blog.app import mongo
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

class User(UserMixin):
    def __init__(self, username, email, password=None, password_hash=None, bio=None, is_admin=False, _id=None, date_joined=None, last_login=None):
        self.username = username
        self.email = email
        self.bio = bio
        self.is_admin = is_admin
        self._id = _id
        self.date_joined = date_joined or datetime.utcnow()
        self.last_login = last_login or datetime.utcnow()
        if password_hash is not None:
            self.password_hash = password_hash
        elif password is not None:
            self.set_password(password)
        else:
            self.password_hash = None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create(data):
        data['password_hash'] = generate_password_hash(data['password'])
        del data['password']
        data['date_joined'] = datetime.utcnow()
        data['last_login'] = datetime.utcnow()
        data['is_admin'] = data.get('is_admin', False)
        result = mongo.db.users.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def get_by_id(user_id):
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            user_data = dict(user)
            user_id_val = user_data.pop('_id', None)
            return User(**user_data, _id=user_id_val)
        return None

    @staticmethod
    def find_by_email(email):
        user = mongo.db.users.find_one({'email': email})
        if user:
            user_data = dict(user)
            user_id_val = user_data.pop('_id', None)
            return User(**user_data, _id=user_id_val)
        return None

    @staticmethod
    def find_by_username(username):
        user = mongo.db.users.find_one({'username': username})
        if user:
            user_data = dict(user)
            user_id_val = user_data.pop('_id', None)
            return User(**user_data, _id=user_id_val)
        return None

    @staticmethod
    def update_last_login(user_id):
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'last_login': datetime.utcnow()}})

    @staticmethod
    def update(user_id, data):
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': data})

    @staticmethod
    def delete(user_id):
        # Delete all comments by the user
        mongo.db.comments.delete_many({'user_id': user_id})
        # Delete all posts by the user
        mongo.db.posts.delete_many({'user_id': user_id})
        # Delete the user
        mongo.db.users.delete_one({'_id': ObjectId(user_id)})

    def get_id(self):
        return str(self._id)

    @property
    def id(self):
        return str(self._id) if self._id is not None else None

    def __repr__(self):
        return f'<User {self.username}>'
