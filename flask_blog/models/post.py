from datetime import datetime
from flask_blog.app import mongo
from bson.objectid import ObjectId

# Association table for posts and tags
post_tags = mongo.db.post_tags

class Post:
    @staticmethod
    def create(data):
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        result = mongo.db.posts.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def get_by_id(post_id):
        return mongo.db.posts.find_one({'_id': ObjectId(post_id)})

    @staticmethod
    def update(post_id, data):
        data['updated_at'] = datetime.utcnow()
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {'$set': data})

    @staticmethod
    def delete(post_id):
        mongo.db.posts.delete_one({'_id': ObjectId(post_id)})

class Category:
    @staticmethod
    def create(data):
        result = mongo.db.categories.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def get_by_id(category_id):
        return mongo.db.categories.find_one({'_id': ObjectId(category_id)})

class Tag:
    @staticmethod
    def create(data):
        result = mongo.db.tags.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def get_by_id(tag_id):
        return mongo.db.tags.find_one({'_id': ObjectId(tag_id)})
